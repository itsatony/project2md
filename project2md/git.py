# project2md/git.py
from pathlib import Path
from typing import Optional, List
import git
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError
import logging
from rich.progress import Progress
import tempfile
import shutil
import os

from .config import Config

logger = logging.getLogger(__name__)

class GitError(Exception):
    """Custom exception for Git-related errors."""
    pass

class GitHandler:
    """Handles Git repository operations including cloning and validation."""
    
    def __init__(self, config: Config, progress: Progress):
        self.config = config
        self.progress = progress
        self._repo: Optional[git.Repo] = None
        self._temp_dir: Optional[Path] = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._cleanup_temp_dir()
        return False  # Don't suppress exceptions

    def cleanup(self):
        """Explicit cleanup method."""
        self._cleanup_temp_dir()

    def prepare_repository(self, force: bool = False) -> Path:
        """
        Prepare the repository for processing. Either clone a remote repository
        or validate and use a local one.
        
        Args:
            force: If True, allow processing of non-git directories
            
        Returns:
            Path to the repository root
            
        Raises:
            GitError: If there are issues with the repository
        """
        try:
            if self.config.repo_url:
                return self._clone_repository()
            else:
                return self._validate_local_repository(force)
        except Exception as e:
            raise GitError(f"Failed to prepare repository: {str(e)}")

    def _clone_repository(self) -> Path:
        """Clone a remote repository to a temporary directory."""
        try:
            logger.info(f"Cloning repository from {self.config.repo_url}")
            
            # Always use a temporary directory for remote repositories
            self._temp_dir = Path(tempfile.mkdtemp(prefix='project2md_'))
            logger.debug(f"Created temporary directory: {self._temp_dir}")
            
            # Clone the repository with specific branch
            self._repo = git.Repo.clone_from(
                self.config.repo_url,
                self._temp_dir,
                progress=self._progress_printer,
                branch=self.config.branch
            )
            
            logger.info(f"Repository cloned successfully on branch {self.config.branch}")
            return self._temp_dir

        except GitCommandError as e:
            self._cleanup_temp_dir()
            if "Remote branch not found" in str(e):
                raise GitError(f"Branch '{self.config.branch}' not found in repository")
            raise GitError(f"Git clone failed: {str(e)}")
        except Exception as e:
            self._cleanup_temp_dir()
            raise GitError(f"Failed to clone repository: {str(e)}")

    def _cleanup_temp_dir(self) -> None:
        """Clean up temporary directory if it exists."""
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
                logger.debug(f"Cleaned up temporary directory: {self._temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory {self._temp_dir}: {e}")

    def __del__(self):
        """Ensure temporary directory is cleaned up."""
        self._cleanup_temp_dir()

    def _validate_local_repository(self, force: bool = False) -> Path:
        """Validate and prepare a local repository or directory."""
        try:
            path = self.config.target_dir.resolve()
            
            if not path.exists():
                raise GitError(f"Directory does not exist: {path}")
            
            if force:
                logger.info("Force flag used - processing directory without Git validation")
                return path
            
            try:
                self._repo = git.Repo(path)
                logger.info("Valid Git repository found")
                
                # Only attempt branch switching if explicitly requested
                if self.config.branch != "main" and self.config.branch != self.get_current_branch():
                    try:
                        if self.config.branch in [b.name for b in self._repo.refs]:
                            self._repo.git.checkout(self.config.branch)
                            logger.info(f"Switched to branch: {self.config.branch}")
                        else:
                            raise GitError(f"Branch '{self.config.branch}' not found")
                    except GitCommandError as e:
                        raise GitError(f"Failed to switch to branch '{self.config.branch}': {str(e)}")
                        
            except InvalidGitRepositoryError:
                logger.info("Not a Git repository - processing as regular directory")
                if not force:
                    message = (
                        f"Directory is not a Git repository: {path}\n"
                        "Use --force to process it anyway"
                    )
                    raise GitError(message)
                return path
            
            return path

        except Exception as e:
            if isinstance(e, GitError):
                raise
            raise GitError(f"Failed to validate local repository: {str(e)}")

    def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        if not self._repo:
            return "unknown"
        try:
            return self._repo.active_branch.name
        except TypeError:  # HEAD might be detached
            return "detached-head"
        except Exception as e:
            logger.warning(f"Failed to get current branch: {e}")
            return "unknown"

    def get_repo_info(self) -> dict:
        """Get repository information for documentation."""
        if not self._repo:
            return {
                "branch": "unknown",
                "is_git_repo": False
            }
        
        return {
            "branch": self.get_current_branch(),
            "is_git_repo": True,
            "has_uncommitted_changes": self._repo.is_dirty(),
            "remotes": [remote.name for remote in self._repo.remotes],
            "root_path": str(self._repo.working_dir)
        }

    def _progress_printer(self, op_code: int, cur_count: int, max_count: int, message: str) -> None:
        """Callback for Git clone progress."""
        if max_count:
            percentage = cur_count / max_count * 100
            self.progress.console.print(
                f"Clone progress: {percentage:.1f}% ({message})",
                end="\r"
            )

    def get_available_branches(self) -> List[str]:
        """Get list of available branches."""
        if not self._repo:
            return []
        try:
            return [ref.name for ref in self._repo.references if not ref.name.startswith('origin/')]
        except Exception as e:
            logger.warning(f"Failed to get branches: {e}")
            return []