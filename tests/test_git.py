# tests/test_git.py
import pytest
from pathlib import Path
import git
from git.exc import GitCommandError
from unittest.mock import Mock, patch
from rich.progress import Progress
import tempfile

from project2md.git import GitHandler, GitError
from project2md.config import Config

@pytest.fixture
def mock_progress():
    return Mock(spec=Progress)

@pytest.fixture
def config():
    return Config()

@pytest.fixture
def git_handler(config, mock_progress):
    return GitHandler(config, mock_progress)

@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary Git repository."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    repo = git.Repo.init(repo_path)
    
    # Create a test file and commit it
    test_file = repo_path / "test.txt"
    test_file.write_text("Test content")
    repo.index.add(["test.txt"])
    repo.index.commit("Initial commit")
    
    return repo_path

def test_validate_local_repository_success(git_handler, temp_git_repo):
    git_handler.config.target_dir = temp_git_repo
    result = git_handler._validate_local_repository()
    assert result == temp_git_repo

def test_validate_local_repository_not_git(git_handler, tmp_path):
    git_handler.config.target_dir = tmp_path
    with pytest.raises(GitError, match="Directory is not a Git repository"):
        git_handler._validate_local_repository()

def test_validate_local_repository_force(git_handler, tmp_path):
    git_handler.config.target_dir = tmp_path
    result = git_handler._validate_local_repository(force=True)
    assert result == tmp_path

def test_validate_local_repository_nonexistent(git_handler, tmp_path):
    git_handler.config.target_dir = tmp_path / "nonexistent"
    with pytest.raises(GitError, match="Directory does not exist"):
        git_handler._validate_local_repository()

@patch('git.Repo.clone_from')
def test_clone_repository_success(mock_clone, git_handler, tmp_path):
    """Test that remote repositories are cloned to a temporary directory."""
    git_handler.config.repo_url = "https://github.com/test/repo.git"
    mock_clone.return_value = Mock(spec=git.Repo)
    
    result = git_handler._clone_repository()
    
    # Verify we got a temporary directory
    assert result.parent == Path('/tmp')
    assert result.name.startswith('project2md_')
    assert mock_clone.called
    assert mock_clone.call_args[1]['branch'] == git_handler.config.branch

@patch('git.Repo.clone_from')
def test_clone_repository_failure(mock_clone, git_handler, tmp_path):
    git_handler.config.repo_url = "https://github.com/test/repo.git"
    git_handler.config.target_dir = tmp_path / "cloned"
    mock_clone.side_effect = GitCommandError('clone', 'error')
    
    with pytest.raises(GitError, match="Git clone failed"):
        git_handler._clone_repository()

@patch('git.Repo.clone_from')
def test_clone_repository_cleanup(mock_clone, git_handler):
    """Test that temporary directories are cleaned up after errors."""
    git_handler.config.repo_url = "https://github.com/test/repo.git"
    mock_clone.side_effect = GitCommandError('clone', 'error')
    
    with pytest.raises(GitError):
        git_handler._clone_repository()
    
    # Verify temp dir was cleaned up
    assert git_handler._temp_dir is None or not git_handler._temp_dir.exists()

def test_validate_local_repository_branch_switching(git_handler, temp_git_repo):
    """Test branch switching in local repository."""
    # Create a new branch in the test repo
    repo = git.Repo(temp_git_repo)
    repo.create_head('test-branch')
    
    git_handler.config.target_dir = temp_git_repo
    git_handler.config.branch = 'test-branch'
    
    result = git_handler._validate_local_repository()
    assert result == temp_git_repo
    assert git_handler.get_current_branch() == 'test-branch'

def test_validate_local_repository_nonexistent_branch(git_handler, temp_git_repo):
    """Test handling of nonexistent branch."""
    git_handler.config.target_dir = temp_git_repo
    git_handler.config.branch = 'nonexistent-branch'
    
    with pytest.raises(GitError, match="Branch 'nonexistent-branch' not found"):
        git_handler._validate_local_repository()

def test_repository_cleanup_on_deletion(config, mock_progress):
    """Test cleanup of temporary directory."""
    with GitHandler(config, mock_progress) as git_handler:
        git_handler.config.repo_url = "https://github.com/test/repo.git"
        
        # Create a fake temp directory
        temp_dir = Path(tempfile.mkdtemp(prefix='project2md_test_'))
        git_handler._temp_dir = temp_dir
        
        # Verify directory exists
        assert temp_dir.exists()
        
    # Verify cleanup after context exit
    assert not temp_dir.exists()

def test_get_current_branch(git_handler, temp_git_repo):
    git_handler.config.target_dir = temp_git_repo
    git_handler._validate_local_repository()
    
    branch = git_handler.get_current_branch()
    assert branch == "master" or branch == "main"

def test_get_repo_info(git_handler, temp_git_repo):
    git_handler.config.target_dir = temp_git_repo
    git_handler._validate_local_repository()
    
    info = git_handler.get_repo_info()
    assert info["is_git_repo"] is True
    assert "branch" in info
    assert "has_uncommitted_changes" in info
    assert "remotes" in info
    assert "root_path" in info

def test_get_repo_info_no_repo(git_handler):
    info = git_handler.get_repo_info()
    assert info["is_git_repo"] is False
    assert info["branch"] == "unknown"

def test_get_repo_info_complete(git_handler, temp_git_repo):
    """Test complete repository info retrieval."""
    git_handler.config.target_dir = temp_git_repo
    git_handler._validate_local_repository()
    
    info = git_handler.get_repo_info()
    assert isinstance(info, dict)
    assert all(key in info for key in ['branch', 'is_git_repo', 'has_uncommitted_changes', 'remotes', 'root_path'])
    assert info['is_git_repo'] is True
    assert isinstance(info['has_uncommitted_changes'], bool)
    assert isinstance(info['remotes'], list)
    assert isinstance(info['root_path'], str)