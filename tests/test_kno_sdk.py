"""
Test script for KNO SDK components.
"""

import os
import sys
from pathlib import Path
import unittest
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from kno_sdk import KNO, GitHubConnector, EmbeddingEngine, CacheManager, VersionControl

class TestKNO(unittest.TestCase):
    """Test KNO SDK components."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        load_dotenv()
        cls.api_token = os.getenv("GITHUB_TOKEN")
        if not cls.api_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        cls.test_repo = "owner/repo"  # Replace with actual test repository
        cls.cache_dir = Path.home() / ".kno_test_cache"
        
    def setUp(self):
        """Set up before each test."""
        self.kno = KNO(api_token=self.api_token, cache_dir=str(self.cache_dir))
        
    def test_github_connector(self):
        """Test GitHub connector functionality."""
        # Test repository connection
        repo = self.kno.github.connect(self.test_repo)
        self.assertIsNotNone(repo)
        
        # Test file listing
        files = self.kno.github.list_files(repo)
        self.assertIsInstance(files, list)
        
        # Test file content retrieval
        if files:
            content = self.kno.github.get_file_content(repo, files[0])
            self.assertIsNotNone(content)
            
    def test_embedding_engine(self):
        """Test embedding engine functionality."""
        # Test single embedding generation
        test_text = "This is a test sentence."
        embedding = self.kno.embeddings.generate(test_text)
        self.assertIsInstance(embedding, dict)
        self.assertIn("embedding", embedding)
        
        # Test batch embedding generation
        test_texts = ["Test 1", "Test 2", "Test 3"]
        embeddings = self.kno.embeddings.batch_generate(test_texts)
        self.assertEqual(len(embeddings), len(test_texts))
        
        # Test similarity calculation
        similarity = self.kno.embeddings.similarity(embeddings[0], embeddings[1])
        self.assertIsInstance(similarity, float)
        
    def test_cache_manager(self):
        """Test cache manager functionality."""
        # Test embedding storage and retrieval
        test_path = "test_file.txt"
        test_embedding = self.kno.embeddings.generate("Test content")
        
        self.kno.cache.store_embedding(test_path, test_embedding)
        retrieved = self.kno.cache.get_embedding(test_path)
        self.assertIsNotNone(retrieved)
        
        # Test interaction storage and retrieval
        test_query = "Test query"
        test_response = "Test response"
        self.kno.cache.store_interaction(test_query, test_response)
        retrieved = self.kno.cache.get_interaction(test_query)
        self.assertIsNotNone(retrieved)
        
        # Test similarity search
        results = self.kno.cache.query_similar(test_query)
        self.assertIsInstance(results, list)
        
    def test_version_control(self):
        """Test version control functionality."""
        # Test change tracking
        repo = self.kno.github.connect(self.test_repo)
        
        def test_callback(repo, file_path, old_content, new_content):
            self.kno.version.track_change(repo, file_path, old_content, new_content)
            
        self.kno.version.watch(repo, test_callback)
        
        # Test history retrieval
        history = self.kno.version.get_history(repo)
        self.assertIsInstance(history, list)
        
        # Clean up
        self.kno.version.stop_watching(repo)
        
    def test_integration(self):
        """Test full SDK integration."""
        # Connect to repository
        repo = self.kno.connect_repository(self.test_repo)
        
        # Generate embeddings
        embeddings = repo.generate_embeddings()
        self.assertIsInstance(embeddings, dict)
        
        # Access cache
        cache = repo.get_cache()
        self.assertIsNotNone(cache)
        
        # Test change watching
        def test_callback(repo, file_path, old_content, new_content):
            print(f"File changed: {file_path}")
            
        repo.watch_changes(test_callback)

if __name__ == "__main__":
    unittest.main() 