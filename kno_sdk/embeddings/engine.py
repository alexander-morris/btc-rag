"""
Embedding engine for generating and managing file embeddings.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json

class EmbeddingEngine:
    """Handles embedding generation and management."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding engine.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model = SentenceTransformer(model_name)
        self.cache_dir = Path.home() / ".kno_embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def generate(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate embedding for content.
        
        Args:
            content: Text content to embed
            metadata: Optional metadata about the content
            
        Returns:
            Dictionary containing embedding and metadata
        """
        # Generate embedding
        embedding = self.model.encode(content, convert_to_tensor=False)
        
        # Create result dictionary
        result = {
            "embedding": embedding.tolist(),
            "metadata": metadata or {},
            "content_hash": hash(content)
        }
        
        return result
    
    def batch_generate(
        self,
        contents: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for multiple contents.
        
        Args:
            contents: List of text contents to embed
            metadata_list: Optional list of metadata dictionaries
            
        Returns:
            List of embedding results
        """
        # Generate embeddings in batch
        embeddings = self.model.encode(contents, convert_to_tensor=False)
        
        # Create results
        results = []
        for i, (content, embedding) in enumerate(zip(contents, embeddings)):
            metadata = metadata_list[i] if metadata_list else None
            result = {
                "embedding": embedding.tolist(),
                "metadata": metadata or {},
                "content_hash": hash(content)
            }
            results.append(result)
            
        return results
    
    def save_embedding(self, embedding: Dict[str, Any], file_path: str) -> None:
        """
        Save embedding to cache.
        
        Args:
            embedding: Embedding dictionary to save
            file_path: Path to save the embedding
        """
        cache_path = self.cache_dir / f"{file_path.replace('/', '_')}.json"
        with open(cache_path, 'w') as f:
            json.dump(embedding, f)
            
    def load_embedding(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load embedding from cache.
        
        Args:
            file_path: Path to load the embedding from
            
        Returns:
            Embedding dictionary if found, None otherwise
        """
        cache_path = self.cache_dir / f"{file_path.replace('/', '_')}.json"
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return None
    
    def similarity(self, embedding1: Dict[str, Any], embedding2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two embeddings.
        
        Args:
            embedding1: First embedding dictionary
            embedding2: Second embedding dictionary
            
        Returns:
            Similarity score between 0 and 1
        """
        vec1 = np.array(embedding1["embedding"])
        vec2 = np.array(embedding2["embedding"])
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))) 