import os
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np

@dataclass
class KnoCacheEntry:
    """Represents a single .kno cache entry."""
    file_path: str
    embedding_type: str
    subsystem: str
    hash: str
    timestamp: float
    embeddings: List[float]
    metadata: Dict[str, Any]

class KnoCacheManager:
    """Manages the .kno cache system for file-level embeddings."""
    
    def __init__(self, cache_root: str = ".kno"):
        """Initialize the cache manager.
        
        Args:
            cache_root: Root directory for the cache
        """
        self.cache_root = Path(cache_root)
        self.metadata_dir = self.cache_root / "metadata"
        self.embeddings_dir = self.cache_root / "embeddings"
        self.temp_dir = self.cache_root / "temp"
        
        # Initialize CodeBERT
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        self.model = AutoModel.from_pretrained("microsoft/codebert-base")
        self.model.eval()
        if torch.cuda.is_available():
            self.model = self.model.cuda()
        
        # Create directory structure
        self._create_directories()
        
        # Initialize processing queue
        self.processing_queue = queue.PriorityQueue()
        self.processing_lock = threading.Lock()
        self.is_processing = False
        
        # Load metadata
        self.file_hashes = self._load_file_hashes()
        self.embedding_types = self._load_embedding_types()
    
    def _create_directories(self):
        """Create the cache directory structure."""
        self.cache_root.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        self.embeddings_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
    
    def _load_file_hashes(self) -> Dict[str, str]:
        """Load file hashes from metadata."""
        hash_file = self.metadata_dir / "file_hashes.json"
        if hash_file.exists():
            with open(hash_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_embedding_types(self) -> Dict[str, Dict[str, Any]]:
        """Load embedding type configurations."""
        types_file = self.metadata_dir / "embedding_types.json"
        if types_file.exists():
            with open(types_file, 'r') as f:
                return json.load(f)
        return {
            "codebert": {
                "description": "General code understanding",
                "model": "microsoft/codebert-base",
                "subsystems": ["validation", "p2p", "mining"]
            }
        }
    
    def _save_file_hashes(self):
        """Save file hashes to metadata."""
        with open(self.metadata_dir / "file_hashes.json", 'w') as f:
            json.dump(self.file_hashes, f)
    
    def _save_embedding_types(self):
        """Save embedding type configurations."""
        with open(self.metadata_dir / "embedding_types.json", 'w') as f:
            json.dump(self.embedding_types, f)
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate hash of a file."""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def _get_cache_path(self, file_path: str, embedding_type: str, subsystem: str) -> Path:
        """Get the path for a cache file."""
        # Convert to Path object and make it absolute
        file_path = Path(file_path).resolve()
        
        # Create a hash of the absolute path to use as the cache file name
        path_hash = hashlib.sha256(str(file_path).encode()).hexdigest()[:16]
        
        # Use the hash as the cache file name
        return self.embeddings_dir / embedding_type / subsystem / f"{path_hash}.kno"
    
    def check_cache(self, file_path: str, embedding_type: str, subsystem: str) -> bool:
        """Check if a valid cache entry exists.
        
        Args:
            file_path: Path to the source file
            embedding_type: Type of embedding (e.g., 'codebert')
            subsystem: Subsystem the file belongs to
            
        Returns:
            True if valid cache exists, False otherwise
        """
        cache_path = self._get_cache_path(file_path, embedding_type, subsystem)
        if not cache_path.exists():
            return False
        
        current_hash = self._get_file_hash(file_path)
        if file_path not in self.file_hashes or self.file_hashes[file_path] != current_hash:
            return False
        
        return True
    
    def get_cache(self, file_path: str, embedding_type: str, subsystem: str) -> Optional[KnoCacheEntry]:
        """Get a cache entry if it exists and is valid.
        
        Args:
            file_path: Path to the source file
            embedding_type: Type of embedding
            subsystem: Subsystem the file belongs to
            
        Returns:
            Cache entry if valid, None otherwise
        """
        if not self.check_cache(file_path, embedding_type, subsystem):
            return None
        
        cache_path = self._get_cache_path(file_path, embedding_type, subsystem)
        with open(cache_path, 'r') as f:
            data = json.load(f)
            return KnoCacheEntry(**data)
    
    def save_cache(self, entry: KnoCacheEntry):
        """Save a cache entry.
        
        Args:
            entry: Cache entry to save
        """
        cache_path = self._get_cache_path(entry.file_path, entry.embedding_type, entry.subsystem)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_path, 'w') as f:
            json.dump({
                "file_path": entry.file_path,
                "embedding_type": entry.embedding_type,
                "subsystem": entry.subsystem,
                "hash": entry.hash,
                "timestamp": entry.timestamp,
                "embeddings": entry.embeddings,
                "metadata": entry.metadata
            }, f)
        
        # Update file hashes
        self.file_hashes[entry.file_path] = entry.hash
        self._save_file_hashes()
    
    def queue_processing(self, file_path: str, embedding_type: str, subsystem: str, priority: int = 0):
        """Queue a file for processing.
        
        Args:
            file_path: Path to the source file
            embedding_type: Type of embedding
            subsystem: Subsystem the file belongs to
            priority: Processing priority (higher = more urgent)
        """
        self.processing_queue.put((priority, (file_path, embedding_type, subsystem)))
        self._start_processing()
    
    def _start_processing(self):
        """Start the background processing thread if not already running."""
        with self.processing_lock:
            if not self.is_processing:
                self.is_processing = True
                threading.Thread(target=self._process_queue, daemon=True).start()
    
    def _process_queue(self):
        """Process the queue of files needing embeddings."""
        with ThreadPoolExecutor(max_workers=4) as executor:
            while True:
                try:
                    priority, (file_path, embedding_type, subsystem) = self.processing_queue.get(timeout=1)
                    
                    # Check if still needed
                    if self.check_cache(file_path, embedding_type, subsystem):
                        continue
                    
                    # Process file
                    executor.submit(self._process_file, file_path, embedding_type, subsystem)
                    
                except queue.Empty:
                    with self.processing_lock:
                        if self.processing_queue.empty():
                            self.is_processing = False
                            break
    
    def _get_file_embeddings(self, file_path: str) -> List[float]:
        """Generate embeddings for a file using CodeBERT.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of embeddings
        """
        # Read file content
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Tokenize and get embeddings
        inputs = self.tokenizer(code, return_tensors="pt", truncation=True, max_length=512, padding=True)
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)  # Average pooling
            
        # Convert to numpy and then to list
        embeddings_np = embeddings.cpu().numpy()
        return embeddings_np[0].tolist()
    
    def _process_file(self, file_path: str, embedding_type: str, subsystem: str):
        """Process a single file to generate embeddings.
        
        Args:
            file_path: Path to the source file
            embedding_type: Type of embedding
            subsystem: Subsystem the file belongs to
        """
        try:
            print(f"\nProcessing file: {file_path}")
            # Generate embeddings
            print("Generating embeddings...")
            embeddings = self._get_file_embeddings(file_path)
            print("Embeddings generated successfully")
            
            # Create cache entry
            print("Creating cache entry...")
            entry = KnoCacheEntry(
                file_path=file_path,
                embedding_type=embedding_type,
                subsystem=subsystem,
                hash=self._get_file_hash(file_path),
                timestamp=time.time(),
                embeddings=embeddings,
                metadata={
                    "file_size": os.path.getsize(file_path),
                    "last_modified": os.path.getmtime(file_path)
                }
            )
            print("Cache entry created")
            
            # Save to cache
            print("Saving to cache...")
            self.save_cache(entry)
            print("Cache entry saved successfully")
            
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            raise  # Re-raise the exception for better error tracking
    
    def scan_directory(self, directory: str, embedding_type: str, subsystem: str):
        """Scan a directory for files needing processing.
        
        Args:
            directory: Directory to scan
            embedding_type: Type of embedding
            subsystem: Subsystem the files belong to
        """
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.cpp', '.h')):
                    file_path = os.path.join(root, file)
                    if not self.check_cache(file_path, embedding_type, subsystem):
                        self.queue_processing(file_path, embedding_type, subsystem)
    
    def get_embedding_types(self) -> List[str]:
        """Get list of available embedding types."""
        return list(self.embedding_types.keys())
    
    def get_subsystems(self, embedding_type: str) -> List[str]:
        """Get list of subsystems for an embedding type."""
        return self.embedding_types.get(embedding_type, {}).get("subsystems", []) 