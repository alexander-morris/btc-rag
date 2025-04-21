"""
Test script for documentation embedding quality assessment.
"""

import os
import sys
from pathlib import Path
import unittest
from dotenv import load_dotenv
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from kno_sdk import KNO

class TestDocumentationEmbeddings(unittest.TestCase):
    """Test documentation embedding quality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        load_dotenv()
        cls.api_token = os.getenv("GITHUB_TOKEN")
        if not cls.api_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        cls.test_repo = os.getenv("TEST_REPO")
        if not cls.test_repo:
            raise ValueError("TEST_REPO environment variable is required")
            
        cls.cache_dir = Path.home() / ".kno_test_cache"
        
        # Initialize SDK
        cls.kno = KNO(api_token=cls.api_token, cache_dir=str(cls.cache_dir))
        cls.repo = cls.kno.connect_repository(cls.test_repo)
        
    def test_documentation_embedding_quality(self):
        """Test the quality of documentation embeddings."""
        # Get all documentation files
        doc_files = [
            f for f in self.repo.github.list_files(self.repo.repo)
            if f.endswith(('.md', '.rst', '.txt')) and 'docs' in f.lower()
        ]
        
        self.assertGreater(len(doc_files), 0, "No documentation files found")
        
        # Generate embeddings for documentation
        doc_embeddings = {}
        for file_path in doc_files:
            content = self.repo.github.get_file_content(self.repo.repo, file_path)
            if content:
                embedding = self.repo.embeddings.generate(content)
                doc_embeddings[file_path] = embedding
                
        self.assertEqual(len(doc_embeddings), len(doc_files), 
                        "Failed to generate embeddings for some documentation files")
        
        # Test semantic similarity between related documentation
        # We expect documentation about similar topics to have high similarity
        similarities = []
        for i, (path1, emb1) in enumerate(doc_embeddings.items()):
            for path2, emb2 in list(doc_embeddings.items())[i+1:]:
                similarity = self.repo.embeddings.similarity(emb1, emb2)
                similarities.append((path1, path2, similarity))
                
        # Sort by similarity
        similarities.sort(key=lambda x: x[2], reverse=True)
        
        # Print top 5 most similar document pairs
        print("\nTop 5 most similar documentation pairs:")
        for path1, path2, sim in similarities[:5]:
            print(f"{path1} <-> {path2}: {sim:.4f}")
            
        # Test query relevance
        test_queries = [
            "What is the main purpose of this project?",
            "How do I install this software?",
            "What are the key features?",
            "How do I contribute to this project?"
        ]
        
        print("\nQuery relevance test:")
        for query in test_queries:
            print(f"\nQuery: {query}")
            # Get query embedding
            query_embedding = self.repo.embeddings.generate(query)
            
            # Find most relevant documents
            relevance_scores = []
            for path, doc_embedding in doc_embeddings.items():
                score = self.repo.embeddings.similarity(query_embedding, doc_embedding)
                relevance_scores.append((path, score))
                
            # Sort by relevance
            relevance_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Print top 3 most relevant documents
            print("Top 3 most relevant documents:")
            for path, score in relevance_scores[:3]:
                print(f"- {path}: {score:.4f}")
                
        # Store embeddings in cache
        cache = self.repo.get_cache()
        for path, embedding in doc_embeddings.items():
            cache.store_embedding(path, embedding)
            
        # Test cache retrieval
        for path in doc_embeddings:
            cached = cache.get_embedding(path)
            self.assertIsNotNone(cached, f"Failed to retrieve embedding for {path}")
            self.assertEqual(
                len(cached["embedding"]),
                len(doc_embeddings[path]["embedding"]),
                f"Embedding size mismatch for {path}"
            )
            
    def test_documentation_change_detection(self):
        """Test documentation change detection and embedding updates."""
        # Get documentation files
        doc_files = [
            f for f in self.repo.github.list_files(self.repo.repo)
            if f.endswith(('.md', '.rst', '.txt')) and 'docs' in f.lower()
        ]
        
        if not doc_files:
            self.skipTest("No documentation files found")
            
        # Set up change detection
        changes_detected = []
        def on_change(repo, file_path, old_content, new_content):
            changes_detected.append((file_path, len(old_content), len(new_content)))
            
        self.repo.watch_changes(on_change)
        
        # Simulate a change (in a real scenario, this would be an actual file change)
        test_file = doc_files[0]
        content = self.repo.github.get_file_content(self.repo.repo, test_file)
        if content:
            # Modify content
            modified_content = content + "\n\nThis is a test modification."
            
            # Track the change
            self.repo.version.track_change(
                self.repo.repo,
                test_file,
                content,
                modified_content
            )
            
            # Generate new embedding
            new_embedding = self.repo.embeddings.generate(modified_content)
            
            # Store in cache
            cache = self.repo.get_cache()
            cache.store_embedding(test_file, new_embedding)
            
            # Verify change was detected
            self.assertEqual(len(changes_detected), 1)
            self.assertEqual(changes_detected[0][0], test_file)
            
        # Clean up
        self.repo.version.stop_watching(self.repo.repo)

if __name__ == "__main__":
    unittest.main() 