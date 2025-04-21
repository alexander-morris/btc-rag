"""
Basic example demonstrating KNO SDK usage.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from kno_sdk import KNO

def main():
    """Run basic SDK example."""
    # Load environment variables
    load_dotenv()
    
    # Initialize SDK
    kno = KNO(
        api_token=os.getenv("GITHUB_TOKEN"),
        cache_dir=str(Path.home() / ".kno_example_cache")
    )
    
    # Connect to repository
    repo = kno.connect_repository(os.getenv("TEST_REPO"))
    print(f"Connected to repository: {repo.repo_name}")
    
    # Generate embeddings for all files
    print("Generating embeddings...")
    embeddings = repo.generate_embeddings()
    print(f"Generated embeddings for {len(embeddings)} files")
    
    # Store embeddings in cache
    print("Storing embeddings in cache...")
    cache = repo.get_cache()
    for file_path, embedding in embeddings.items():
        cache.store_embedding(file_path, embedding)
    print("Embeddings stored in cache")
    
    # Query similar content
    print("\nQuerying similar content...")
    query = "What is the main functionality of this repository?"
    results = cache.query_similar(query)
    print(f"Found {len(results)} similar items:")
    for result in results:
        print(f"- {result['document']} (distance: {result['distance']:.4f})")
    
    # Set up change watching
    print("\nSetting up change watching...")
    def on_change(repo, file_path, old_content, new_content):
        print(f"\nFile changed: {file_path}")
        if old_content:
            print(f"Old content length: {len(old_content)}")
        if new_content:
            print(f"New content length: {len(new_content)}")
        
    repo.watch_changes(on_change)
    print("Change watching active. Press Ctrl+C to stop.")
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping change watching...")

if __name__ == "__main__":
    main() 