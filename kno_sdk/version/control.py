"""
Version control for tracking file changes and managing updates.
"""

from typing import Dict, Any, Optional, Callable
from github import Github
from github.Repository import Repository as GitHubRepo
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import hashlib
from datetime import datetime
import json
from pathlib import Path

class VersionControl:
    """Manages version tracking and change detection."""
    
    def __init__(self):
        """Initialize version control."""
        self.observers = {}
        self.history_dir = Path.home() / ".kno_history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
    def watch(self, repo: GitHubRepo, callback: Callable) -> None:
        """
        Watch repository for changes.
        
        Args:
            repo: GitHub repository object
            callback: Function to call when changes are detected
        """
        if repo.full_name in self.observers:
            return
            
        # Create event handler
        handler = RepositoryEventHandler(repo, callback)
        observer = Observer()
        observer.schedule(handler, str(self.history_dir), recursive=True)
        observer.start()
        
        self.observers[repo.full_name] = observer
        
    def stop_watching(self, repo: GitHubRepo) -> None:
        """
        Stop watching repository for changes.
        
        Args:
            repo: GitHub repository object
        """
        if repo.full_name in self.observers:
            self.observers[repo.full_name].stop()
            del self.observers[repo.full_name]
            
    def track_change(
        self,
        repo: GitHubRepo,
        file_path: str,
        old_content: str,
        new_content: str
    ) -> None:
        """
        Track a file change.
        
        Args:
            repo: GitHub repository object
            file_path: Path of changed file
            old_content: Previous content
            new_content: New content
        """
        # Create change record
        change = {
            "repo": repo.full_name,
            "file_path": file_path,
            "old_hash": hashlib.md5(old_content.encode()).hexdigest(),
            "new_hash": hashlib.md5(new_content.encode()).hexdigest(),
            "timestamp": str(datetime.now())
        }
        
        # Save to history
        history_file = self.history_dir / f"{repo.full_name.replace('/', '_')}.json"
        history = []
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
                
        history.append(change)
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
    def get_history(
        self,
        repo: GitHubRepo,
        file_path: Optional[str] = None
    ) -> list:
        """
        Get change history for repository or file.
        
        Args:
            repo: GitHub repository object
            file_path: Optional specific file path
            
        Returns:
            List of change records
        """
        history_file = self.history_dir / f"{repo.full_name.replace('/', '_')}.json"
        if not history_file.exists():
            return []
            
        with open(history_file, 'r') as f:
            history = json.load(f)
            
        if file_path:
            return [h for h in history if h["file_path"] == file_path]
        return history

class RepositoryEventHandler(FileSystemEventHandler):
    """Handles file system events for repository watching."""
    
    def __init__(self, repo: GitHubRepo, callback: Callable):
        """
        Initialize event handler.
        
        Args:
            repo: GitHub repository object
            callback: Function to call when changes are detected
        """
        self.repo = repo
        self.callback = callback
        self.last_content = {}
        
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            file_path = event.src_path
            try:
                # Get current content
                content = self.repo.get_contents(file_path).decoded_content.decode('utf-8')
                
                # Compare with last content
                if file_path in self.last_content:
                    old_content = self.last_content[file_path]
                    if old_content != content:
                        self.callback(self.repo, file_path, old_content, content)
                        
                # Update last content
                self.last_content[file_path] = content
            except Exception as e:
                print(f"Error handling file modification: {e}")
                
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            file_path = event.src_path
            try:
                content = self.repo.get_contents(file_path).decoded_content.decode('utf-8')
                self.callback(self.repo, file_path, "", content)
                self.last_content[file_path] = content
            except Exception as e:
                print(f"Error handling file creation: {e}")
                
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            file_path = event.src_path
            try:
                if file_path in self.last_content:
                    old_content = self.last_content[file_path]
                    self.callback(self.repo, file_path, old_content, "")
                    del self.last_content[file_path]
            except Exception as e:
                print(f"Error handling file deletion: {e}") 