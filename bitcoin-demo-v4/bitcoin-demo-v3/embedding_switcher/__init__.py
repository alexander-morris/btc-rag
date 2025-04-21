from typing import Dict, Any, List, Optional
from .base import BaseEmbeddingAdapter
from .codebert import CodeBERTAdapter

class EmbeddingSwitcher:
    """A flexible embedding switcher for code analysis."""
    
    def __init__(self):
        """Initialize the embedding switcher."""
        self.embedders = {}
    
    def register_adapter(self, name: str, adapter: BaseEmbeddingAdapter):
        """Register an embedding adapter.
        
        Args:
            name: Name of the adapter
            adapter: The adapter instance
        """
        self.embedders[name] = adapter
    
    def get_embeddings(self, name: str) -> BaseEmbeddingAdapter:
        """Get an embedder by name.
        
        Args:
            name: The name of the embedder
            
        Returns:
            An initialized embedder instance
        """
        if name not in self.embedders:
            raise ValueError(f"Embedder '{name}' not found")
        
        return self.embedders[name]
    
    def list_embedders(self) -> List[str]:
        """List all available embedders.
        
        Returns:
            List of embedder names
        """
        return list(self.embedders.keys())

__all__ = ['CodeBERTAdapter', 'EmbeddingSwitcher'] 