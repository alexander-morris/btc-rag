from typing import List, Dict, Any
from abc import ABC, abstractmethod

class BaseEmbeddingAdapter(ABC):
    """Base class for embedding adapters."""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of documents.
        
        Args:
            texts: List of text documents to embed
            
        Returns:
            List of embeddings as float lists
        """
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Create an embedding for a single query.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding as a list of floats
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model.
        
        Returns:
            Dictionary with model information
        """
        pass 