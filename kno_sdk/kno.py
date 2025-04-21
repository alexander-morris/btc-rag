"""
Main KNO SDK class providing the primary interface for users.
"""

from typing import Optional, Dict, Any
from pathlib import Path
import os
from dotenv import load_dotenv

from .github.connector import GitHubConnector
from .embeddings.engine import EmbeddingEngine
from .cache.manager import CacheManager
from .version.control import VersionControl

class KNO:
    """Main KNO SDK class providing access to all functionality."""
    
    def __init__(self, api_token: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the KNO SDK.
        
        Args:
            api_token: GitHub API token. If None, will try to load from environment.
            cache_dir: Directory for local cache storage. If None, will use default.
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize components
        self.api_token = api_token or os.getenv("GITHUB_TOKEN")
        if not self.api_token:
            raise ValueError("GitHub API token is required")
            
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".kno_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.github = GitHubConnector(self.api_token)
        self.embeddings = EmbeddingEngine()
        self.cache = CacheManager(str(self.cache_dir))
        self.version = VersionControl()
        
    def connect_repository(self, repo_name: str) -> "Repository":
        """
        Connect to a GitHub repository.
        
        Args:
            repo_name: Repository name in format 'owner/repo'
            
        Returns:
            Repository object for interacting with the connected repository
        """
        return Repository(
            repo_name=repo_name,
            github=self.github,
            embeddings=self.embeddings,
            cache=self.cache,
            version=self.version
        )

class Repository:
    """Represents a connected GitHub repository with KNO functionality."""
    
    def __init__(
        self,
        repo_name: str,
        github: GitHubConnector,
        embeddings: EmbeddingEngine,
        cache: CacheManager,
        version: VersionControl
    ):
        self.repo_name = repo_name
        self.github = github
        self.embeddings = embeddings
        self.cache = cache
        self.version = version
        
        # Connect to repository
        self.repo = self.github.connect(repo_name)
        
    def generate_embeddings(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate embeddings for repository files.
        
        Args:
            file_path: Optional specific file path to process
            
        Returns:
            Dictionary containing embedding results
        """
        if file_path:
            files = [file_path]
        else:
            files = self.github.list_files(self.repo)
            
        results = {}
        for file in files:
            content = self.github.get_file_content(self.repo, file)
            embedding = self.embeddings.generate(content)
            results[file] = embedding
            
        return results
    
    def get_cache(self) -> CacheManager:
        """Get the cache manager for this repository."""
        return self.cache
    
    def watch_changes(self, callback: callable) -> None:
        """
        Watch for changes in the repository.
        
        Args:
            callback: Function to call when changes are detected
        """
        self.version.watch(self.repo, callback) 