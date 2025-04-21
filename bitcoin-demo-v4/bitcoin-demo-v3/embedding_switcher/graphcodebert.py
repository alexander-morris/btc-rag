from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
import time
from .base import BaseEmbeddingAdapter

class GraphCodeBERTAdapter(BaseEmbeddingAdapter):
    """Adapter for GraphCodeBERT model."""
    
    def __init__(self, model_name: str = "microsoft/graphcodebert-base", 
                 max_length: int = 512,
                 batch_size: int = 32,
                 device: str = None,
                 **model_kwargs: Any):
        """Initialize GraphCodeBERT model.
        
        Args:
            model_name: HuggingFace model name
            max_length: Maximum sequence length
            batch_size: Batch size for document embedding
            device: Device to run on ('cuda' or 'cpu')
            model_kwargs: Additional model arguments
        """
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_kwargs = model_kwargs
        
        # Initialize metrics
        self._total_tokens = 0
        self._total_time = 0
        
        # Initialize tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name, **model_kwargs)
        
        # Set model to evaluation mode and move to device
        self.model.eval()
        self.model = self.model.to(self.device)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for documents using GraphCodeBERT."""
        start_time = time.time()
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            
            # Tokenize batch
            inputs = self.tokenizer(
                batch_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.max_length
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Update token count
            self._total_tokens += sum(len(t) for t in batch_texts)
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use [CLS] token embedding
                batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                embeddings.extend(batch_embeddings.tolist())
        
        self._total_time += time.time() - start_time
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Create embedding for a single query using GraphCodeBERT."""
        return self.embed_documents([text])[0]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the GraphCodeBERT model."""
        return {
            "name": "GraphCodeBERT",
            "model_name": self.model_name,
            "parameters": "~125M",
            "pre_training": "CodeSearchNet + Graph-based",
            "objective": "MLM + RTD + Graph",
            "best_for": "Code search with structural understanding",
            "features": "Pre-trained with code structure graphs",
            "quality": "Enhanced structural code understanding",
            "link": "https://huggingface.co/microsoft/graphcodebert-base",
            "metrics": {
                "total_tokens_processed": self._total_tokens,
                "avg_tokens_per_second": self._total_tokens / self._total_time if self._total_time > 0 else 0,
                "device": self.device,
                "max_length": self.max_length,
                "batch_size": self.batch_size
            }
        } 