import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from kno_cache import KnoCacheManager, KnoCacheEntry
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_anthropic import ChatAnthropic
import time
from langchain_community.document_loaders import GitLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from dataclasses import dataclass
import git
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import gc
import fnmatch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model cache
_model_cache = {}
_model_lock = threading.Lock()

def get_embedding_model():
    """Get or create embedding model with caching."""
    global _model_cache
    with _model_lock:
        if 'embedding_model' not in _model_cache:
            _model_cache['embedding_model'] = HuggingFaceEmbeddings(
                model_name="microsoft/codebert-base",
                model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
            )
        return _model_cache['embedding_model']

@dataclass
class KnoCacheEntry:
    """A cache entry for storing knowledge about a file."""
    file_path: str
    last_modified: float
    content: str
    embeddings: Optional[List[float]] = None

class BitcoinRAG:
    """Bitcoin RAG system with .kno cache support and optimized performance."""
    
    def __init__(self, repo_path: str, cache_dir: str = ".kno_cache", max_workers: int = 4):
        """Initialize the Bitcoin RAG system.
        
        Args:
            repo_path: Path to the Bitcoin repository
            cache_dir: Root directory for the cache
            max_workers: Maximum number of worker threads
        """
        self.repo_path = repo_path
        self.cache_dir = Path(cache_dir)
        self.max_workers = max_workers
        self.llm = None
        self.retrievers = {}
        self.qa_chains = {}
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        try:
            self.repo = git.Repo(repo_path)
        except git.exc.InvalidGitRepositoryError:
            logger.error(f"Invalid git repository at {repo_path}")
            raise
        except Exception as e:
            logger.error(f"Error initializing repository: {e}")
            raise
        
        self.cache_manager = KnoCacheManager(cache_dir)
        self.embedding_model = get_embedding_model()  # Use cached model
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Define subsystem keywords
        self.subsystem_keywords = {
            'validation': ['validation', 'verify', 'check', 'accept', 'reject'],
            'p2p': ['net', 'network', 'peer', 'connection', 'message'],
            'mining': ['miner', 'mining', 'block', 'pow', 'proof'],
            'wallet': ['wallet', 'key', 'sign', 'transaction', 'address'],
            'consensus': ['consensus', 'rules', 'protocol', 'fork', 'chain']
        }
        
        self._chunk_cache = {}
        self._chunk_cache_lock = threading.Lock()
        
    def _process_file_chunk(self, file_path: str) -> List[Any]:
        """Process a single file and return its chunks."""
        try:
            loader = TextLoader(file_path)
            docs = loader.load()
            chunks = self.text_splitter.split_documents(docs)
            return [chunk for chunk in chunks if chunk.page_content.strip()]
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return []

    def matches_any_pattern(self, path: str, patterns: List[str]) -> bool:
        """Check if a path matches any of the given glob patterns."""
        return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)

    def load_repository(
        self, 
        repo_path: str, 
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None
    ):
        """Load and process the Bitcoin repository with parallel processing and file filtering.
        
        Args:
            repo_path: Path to the repository
            include_patterns: List of glob patterns for files to include (e.g. ["*.cpp", "*.h"])
            exclude_patterns: List of glob patterns for files to exclude (e.g. ["*/test/*"])
        """
        if not os.path.exists(repo_path):
            raise ValueError(f"Repository not found at {repo_path}")
        
        # Default patterns
        if include_patterns is None:
            include_patterns = ["*.cpp", "*.h"]
        if exclude_patterns is None:
            exclude_patterns = []
        
        logger.info(f"Loading repository with include patterns: {include_patterns}, exclude patterns: {exclude_patterns}")
        
        # Get all relevant files
        cpp_files = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Check if file matches include patterns
                if not self.matches_any_pattern(rel_path, include_patterns):
                    continue
                
                # Check if file matches exclude patterns
                if self.matches_any_pattern(rel_path, exclude_patterns):
                    logger.debug(f"Excluding file: {rel_path}")
                    continue
                
                cpp_files.append(file_path)
                logger.debug(f"Including file: {rel_path}")
        
        logger.info(f"Found {len(cpp_files)} files matching patterns")
        
        chunks = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._process_file_chunk, file): file 
                for file in cpp_files
            }
            
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    file_chunks = future.result()
                    chunks.extend(file_chunks)
                except Exception as e:
                    logger.error(f"Error processing {file}: {e}")
        
        # Cache the chunks
        with self._chunk_cache_lock:
            self._chunk_cache['all_chunks'] = chunks
        
        # Save chunks to disk
        chunk_path = self.cache_dir / "chunks.json"
        with open(chunk_path, "w") as f:
            json.dump([{
                "page_content": doc.page_content,
                "metadata": doc.metadata
            } for doc in chunks], f)
        
        return chunks

    def create_embeddings(self, subsystem: str):
        """Create embeddings for a specific subsystem with optimized memory usage."""
        logger.info(f"Processing subsystem: {subsystem}")
        
        # Try to load from cache first
        cache_key = f"embeddings_{subsystem}"
        if cache_key in self._chunk_cache:
            return
        
        # Load or get cached chunks
        chunks = None
        with self._chunk_cache_lock:
            if 'all_chunks' in self._chunk_cache:
                chunks = self._chunk_cache['all_chunks']
        
        if not chunks:
            try:
                chunk_path = self.cache_dir / "chunks.json"
                with open(chunk_path, "r") as f:
                    chunks_data = json.load(f)
                    chunks = [
                        Document(
                            page_content=chunk["page_content"],
                            metadata=chunk["metadata"]
                        )
                        for chunk in chunks_data
                    ]
            except FileNotFoundError:
                chunks = self.load_repository("bitcoin")
        
        # Filter chunks for subsystem
        subsystem_chunks = [
            chunk for chunk in chunks 
            if any(keyword in chunk.page_content.lower() 
                  for keyword in self.subsystem_keywords[subsystem])
        ]
        
        if not subsystem_chunks:
            raise ValueError(f"No chunks found for subsystem {subsystem}")
        
        # Create vectorstore
        vectorstore = FAISS.from_documents(
            documents=subsystem_chunks,
            embedding=self.embedding_model
        )
        
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        
        # Cache results
        with self._chunk_cache_lock:
            self._chunk_cache[cache_key] = {
                'vectorstore': vectorstore,
                'retriever': retriever
            }
        
        self.retrievers[subsystem] = retriever
        
        # Clean up memory
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def setup_qa_chain(self, anthropic_api_key: str):
        """Set up the QA chain with Claude model."""
        if not anthropic_api_key:
            raise ValueError("Anthropic API key is required")
        
        if not self.llm:
            self.llm = ChatAnthropic(
                anthropic_api_key=anthropic_api_key,
                model="claude-3-sonnet-20240229",
                temperature=0.2,
                max_tokens=4000
            )
        
        # Create QA chains for each subsystem
        for subsystem, retriever in self.retrievers.items():
            if subsystem not in self.qa_chains:
                prompt_template = """You are an expert Bitcoin Core developer analyzing the codebase. Use the following code context to answer the question. If you cannot answer the question based on the context, say so.

                Context:
                {context}

                Question: {question}

                Answer: Let me analyze the code and provide a detailed response."""
                
                PROMPT = PromptTemplate(
                    template=prompt_template,
                    input_variables=["context", "question"]
                )
                
                self.qa_chains[subsystem] = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=retriever,
                    chain_type_kwargs={
                        "prompt": PROMPT,
                    },
                    return_source_documents=True
                )
    
    def ask_question(self, question: str, subsystem: str = None) -> Dict[str, Any]:
        """Ask a question about the Bitcoin codebase.
        
        Args:
            question: The question to ask
            subsystem: Optional subsystem to focus on
        
        Returns:
            Dict containing the answer and metadata
        """
        if not self.llm:
            raise ValueError("QA chain not set up. Call setup_qa_chain first.")
        
        start_time = time.time()
        
        if subsystem and subsystem not in self.qa_chains:
            raise ValueError(f"Subsystem {subsystem} not found. Available subsystems: {list(self.qa_chains.keys())}")
        
        # If no subsystem specified, try all of them
        subsystems_to_try = [subsystem] if subsystem else list(self.qa_chains.keys())
        
        best_answer = None
        best_confidence = 0
        used_sources = set()
        all_sources = []
        
        for sys in subsystems_to_try:
            try:
                result = self.qa_chains[sys]({"query": question})
                
                # Extract answer and source documents
                answer = result.get("result", "")
                sources = result.get("source_documents", [])
                
                # Calculate confidence based on source document relevance
                confidence = sum(1 for doc in sources if any(keyword in doc.page_content.lower() 
                                                          for keyword in question.lower().split()))
                confidence /= len(sources) if sources else 1
                
                # Track unique sources
                for doc in sources:
                    source_path = doc.metadata.get("source", "")
                    if source_path not in used_sources:
                        used_sources.add(source_path)
                        all_sources.append({
                            "path": source_path,
                            "content": doc.page_content[:200] + "..."  # Truncate for readability
                        })
                
                # Update best answer if this one is better
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_answer = {
                        "answer": answer,
                        "subsystem": sys,
                        "confidence": confidence,
                    }
            
            except Exception as e:
                logger.error(f"Error processing subsystem {sys}: {e}")
                continue
        
        if not best_answer:
            return {
                "error": "No valid answers found",
                "sources": all_sources
            }
        
        # Add metadata to the response
        response = {
            **best_answer,
            "sources": all_sources,
            "query_time": time.time() - start_time,
            "total_sources": len(used_sources)
        }
        
        return response
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache usage."""
        stats = {
            "total_chunks": len(self._chunk_cache.get('all_chunks', [])),
            "cached_subsystems": [k.replace('embeddings_', '') for k in self._chunk_cache.keys() if k.startswith('embeddings_')],
            "memory_usage": {
                "chunk_cache_size": sum(sys.getsizeof(v) for v in self._chunk_cache.values()),
                "model_cache_size": sum(sys.getsizeof(v) for v in _model_cache.values())
            }
        }
        
        if torch.cuda.is_available():
            stats["gpu_memory"] = {
                "allocated": torch.cuda.memory_allocated(),
                "cached": torch.cuda.memory_reserved()
            }
        
        return stats
    
    def cleanup(self):
        """Clean up resources and free memory."""
        # Clear caches
        self._chunk_cache.clear()
        with _model_lock:
            _model_cache.clear()
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Force garbage collection
        gc.collect() 