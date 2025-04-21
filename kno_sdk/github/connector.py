"""
GitHub connector for repository access and management.
"""

from typing import List, Optional, Any, Dict
from github import Github
from github.Repository import Repository as GitHubRepo

class GitHubConnector:
    """Handles GitHub API interactions and repository access."""
    
    def __init__(self, api_token: str):
        """
        Initialize GitHub connector.
        
        Args:
            api_token: GitHub API token
        """
        self.github = Github(api_token)
        
    def connect(self, repo_name: str) -> GitHubRepo:
        """
        Connect to a GitHub repository.
        
        Args:
            repo_name: Repository name in format 'owner/repo'
            
        Returns:
            GitHub repository object
        """
        return self.github.get_repo(repo_name)
    
    def list_files(
        self,
        repo: GitHubRepo,
        path: str = "",
        recursive: bool = True
    ) -> List[str]:
        """
        List files in a repository.
        
        Args:
            repo: GitHub repository object
            path: Starting path in repository
            recursive: Whether to list files recursively
            
        Returns:
            List of file paths
        """
        files = []
        try:
            contents = repo.get_contents(path)
            for content in contents:
                if content.type == "dir" and recursive:
                    files.extend(self.list_files(repo, content.path))
                elif content.type == "file":
                    files.append(content.path)
        except Exception as e:
            print(f"Error listing files: {e}")
        return files
    
    def get_file_content(self, repo: GitHubRepo, path: str) -> Optional[str]:
        """
        Get content of a file from repository.
        
        Args:
            repo: GitHub repository object
            path: Path to file in repository
            
        Returns:
            File content as string, or None if not found
        """
        try:
            content = repo.get_contents(path)
            return content.decoded_content.decode('utf-8')
        except Exception as e:
            print(f"Error getting file content: {e}")
            return None
    
    def get_file_metadata(self, repo: GitHubRepo, path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a file.
        
        Args:
            repo: GitHub repository object
            path: Path to file in repository
            
        Returns:
            Dictionary containing file metadata
        """
        try:
            content = repo.get_contents(path)
            return {
                "path": content.path,
                "sha": content.sha,
                "size": content.size,
                "url": content.url,
                "last_modified": content.last_modified
            }
        except Exception as e:
            print(f"Error getting file metadata: {e}")
            return None 