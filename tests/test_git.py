# tests/test_git.py
import pytest
from pathlib import Path
import git
from git.exc import GitCommandError
from unittest.mock import Mock, patch
from rich.progress import Progress

from reposcribe.git import GitHandler, GitError
from reposcribe.config import Config

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
    git_handler.config.repo_url = "https://github.com/test/repo.git"
    git_handler.config.target_dir = tmp_path / "cloned"
    mock_clone.return_value = Mock(spec=git.Repo)
    
    result = git_handler._clone_repository()
    
    assert result == tmp_path / "cloned"
    mock_clone.assert_called_once()

@patch('git.Repo.clone_from')
def test_clone_repository_failure(mock_clone, git_handler, tmp_path):
    git_handler.config.repo_url = "https://github.com/test/repo.git"
    git_handler.config.target_dir = tmp_path / "cloned"
    mock_clone.side_effect = GitCommandError('clone', 'error')
    
    with pytest.raises(GitError, match="Git clone failed"):
        git_handler._clone_repository()

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