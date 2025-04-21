import os
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import GitLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_anthropic import ChatAnthropic

from embedding_switcher import EmbeddingSwitcher, CodeBERTAdapter

class BitcoinRAG:
    def __init__(self, config_path: str = "embedding_config.yaml"):
        """Initialize the Bitcoin RAG system."""
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.embedding_switcher = EmbeddingSwitcher()
        self.embedding_switcher.register_adapter('codebert', CodeBERTAdapter())
        
        # Initialize LLM
        self.llm = ChatAnthropic(
            model_name="claude-3-sonnet-20240229",
            temperature=0.1,
            max_tokens=4000
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Set up paths
        self.repo_path = Path("bitcoin")
        self.cache_dir = Path("embedding_cache")
        self.cache_dir.mkdir(exist_ok=True)

    def load_repository(self) -> List[Dict[str, Any]]:
        """Load and process the Bitcoin repository."""
        print("Loading Bitcoin repository...")
        
        # Load documents from Git repository
        loader = GitLoader(
            repo_path=str(self.repo_path),
            branch="master",
            file_filter=lambda file_path: file_path.endswith(('.cpp', '.h'))
        )
        documents = loader.load()
        
        # Split documents into chunks
        chunks = []
        for doc in documents:
            doc_chunks = self.text_splitter.split_documents([doc])
            for chunk in doc_chunks:
                chunk.metadata.update({
                    'source': doc.metadata['source'],
                    'file_type': Path(doc.metadata['source']).suffix
                })
            chunks.extend(doc_chunks)
        
        return chunks

    def create_embeddings(self, chunks: List[Dict[str, Any]], 
                         model_name: str = 'codebert') -> FAISS:
        """Create embeddings for the document chunks."""
        print(f"Creating embeddings using {model_name}...")
        
        # Get embedding model
        embeddings = self.embedding_switcher.get_embeddings(model_name)
        
        # Create vector store
        vector_store = FAISS.from_documents(
            chunks,
            embeddings
        )
        
        # Save vector store
        vector_store.save_local(str(self.cache_dir / "faiss_index"))
        
        return vector_store

    def create_subsystem_embeddings(self, chunks: List[Dict[str, Any]], 
                                  subsystem: str) -> FAISS:
        """Create embeddings for a specific subsystem."""
        print(f"Creating embeddings for {subsystem} subsystem...")
        
        # Filter chunks for subsystem
        subsystem_chunks = [
            chunk for chunk in chunks 
            if subsystem in chunk.metadata['source'].lower()
        ]
        
        return self.create_embeddings(subsystem_chunks)

    def setup_qa_chain(self, vector_store: FAISS) -> RetrievalQA:
        """Set up the question answering chain."""
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(
                search_kwargs={"k": 5}
            ),
            return_source_documents=True
        )

    def analyze_code(self, question: str, 
                    subsystem: Optional[str] = None) -> Dict[str, Any]:
        """Analyze Bitcoin code using RAG."""
        # Load or create embeddings
        if (self.cache_dir / "faiss_index").exists():
            vector_store = FAISS.load_local(
                str(self.cache_dir / "faiss_index"),
                self.embedding_switcher.get_embeddings('codebert'),
                allow_dangerous_deserialization=True  # Only for local files we created
            )
        else:
            chunks = self.load_repository()
            if subsystem:
                vector_store = self.create_subsystem_embeddings(chunks, subsystem)
            else:
                vector_store = self.create_embeddings(chunks)
        
        # Set up QA chain
        qa_chain = self.setup_qa_chain(vector_store)
        
        # Generate response
        result = qa_chain({"query": question})
        
        return {
            "answer": result["result"],
            "sources": [
                {
                    "source": doc.metadata["source"],
                    "content": doc.page_content
                }
                for doc in result["source_documents"]
            ]
        }

def main():
    # Initialize RAG system
    rag = BitcoinRAG()
    
    # Example questions
    questions = [
        {
            "question": "How does Bitcoin validate transactions? Explain the process in detail.",
            "subsystem": "validation"
        },
        {
            "question": "Describe the P2P networking protocol implementation in Bitcoin.",
            "subsystem": "net"
        }
    ]
    
    # Process questions
    for q in questions:
        print(f"\nQuestion: {q['question']}")
        result = rag.analyze_code(q["question"], q["subsystem"])
        
        print("\nAnswer:")
        print(result["answer"])
        
        print("\nSources:")
        for source in result["sources"]:
            print(f"- {source['source']}")

if __name__ == "__main__":
    main() 