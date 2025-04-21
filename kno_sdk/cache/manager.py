"""
Cache manager for storing and retrieving embeddings and agent interactions.
"""

from typing import Dict, Any, List, Optional
import chromadb
from chromadb.config import Settings
import json
from pathlib import Path
import hashlib
from datetime import datetime

class CacheManager:
    """Manages caching of embeddings and agent interactions."""
    
    def __init__(self, cache_dir: str):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache storage
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma = chromadb.PersistentClient(
            path=str(self.cache_dir / "chroma"),
            settings=Settings(allow_reset=True)
        )
        
        # Create or get collections
        self.embeddings_collection = self.chroma.get_or_create_collection(
            name="embeddings",
            metadata={"hnsw:space": "cosine"}
        )
        self.interactions_collection = self.chroma.get_or_create_collection(
            name="interactions",
            metadata={"hnsw:space": "cosine"}
        )
        
    def store_embedding(
        self,
        file_path: str,
        embedding: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store embedding in cache.
        
        Args:
            file_path: Path of the file
            embedding: Embedding dictionary
            metadata: Optional additional metadata
        """
        # Create document ID
        doc_id = hashlib.md5(file_path.encode()).hexdigest()
        
        # Store in ChromaDB
        self.embeddings_collection.add(
            ids=[doc_id],
            embeddings=[embedding["embedding"]],
            documents=[file_path],
            metadatas=[{
                "file_path": file_path,
                "content_hash": embedding["content_hash"],
                **(metadata or {})
            }]
        )
        
    def get_embedding(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve embedding from cache.
        
        Args:
            file_path: Path of the file
            
        Returns:
            Embedding dictionary if found, None otherwise
        """
        doc_id = hashlib.md5(file_path.encode()).hexdigest()
        results = self.embeddings_collection.get(
            ids=[doc_id],
            include=["embeddings", "metadatas"]
        )
        
        if results and results["ids"]:
            return {
                "embedding": results["embeddings"][0],
                "metadata": results["metadatas"][0]
            }
        return None
    
    def store_interaction(
        self,
        query: str,
        response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store agent interaction in cache.
        
        Args:
            query: User query
            response: Agent response
            context: Optional context information
        """
        # Create document ID
        doc_id = hashlib.md5(query.encode()).hexdigest()
        
        # Store in ChromaDB
        self.interactions_collection.add(
            ids=[doc_id],
            documents=[query],
            metadatas=[{
                "response": response,
                "context": context or {},
                "timestamp": str(datetime.now())
            }]
        )
        
    def get_interaction(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve interaction from cache.
        
        Args:
            query: User query
            
        Returns:
            Interaction dictionary if found, None otherwise
        """
        doc_id = hashlib.md5(query.encode()).hexdigest()
        results = self.interactions_collection.get(
            ids=[doc_id],
            include=["metadatas"]
        )
        
        if results and results["ids"]:
            return results["metadatas"][0]
        return None
    
    def query_similar(
        self,
        query: str,
        collection: str = "embeddings",
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query for similar items in cache.
        
        Args:
            query: Query string
            collection: Collection to query ("embeddings" or "interactions")
            n_results: Number of results to return
            
        Returns:
            List of similar items with scores
        """
        collection = (
            self.embeddings_collection if collection == "embeddings"
            else self.interactions_collection
        )
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        return [
            {
                "document": doc,
                "metadata": meta,
                "distance": dist
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ] 