"""
Command-line interface for KNO SDK.
"""

import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from . import KNO

def main():
    """Run KNO CLI."""
    parser = argparse.ArgumentParser(description="KNO SDK Command Line Interface")
    parser.add_argument(
        "--token",
        help="GitHub API token",
        default=os.getenv("GITHUB_TOKEN")
    )
    parser.add_argument(
        "--repo",
        help="GitHub repository in format owner/repo",
        required=True
    )
    parser.add_argument(
        "--cache-dir",
        help="Cache directory path",
        default=str(Path.home() / ".kno_cache")
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Embed command
    embed_parser = subparsers.add_parser("embed", help="Generate embeddings")
    embed_parser.add_argument(
        "--file",
        help="Specific file to embed (optional)",
        default=None
    )
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query similar content")
    query_parser.add_argument(
        "query",
        help="Query string"
    )
    query_parser.add_argument(
        "--limit",
        help="Number of results to return",
        type=int,
        default=5
    )
    
    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch for changes")
    
    args = parser.parse_args()
    
    if not args.token:
        parser.error("GitHub token is required. Set GITHUB_TOKEN environment variable or use --token")
    
    # Initialize SDK
    kno = KNO(api_token=args.token, cache_dir=args.cache_dir)
    repo = kno.connect_repository(args.repo)
    
    if args.command == "embed":
        print("Generating embeddings...")
        embeddings = repo.generate_embeddings(args.file)
        print(f"Generated embeddings for {len(embeddings)} files")
        
    elif args.command == "query":
        print(f"Querying: {args.query}")
        cache = repo.get_cache()
        results = cache.query_similar(args.query, n_results=args.limit)
        print(f"\nFound {len(results)} similar items:")
        for result in results:
            print(f"- {result['document']} (distance: {result['distance']:.4f})")
            
    elif args.command == "watch":
        print("Watching for changes...")
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
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 