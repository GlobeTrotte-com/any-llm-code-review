"""Tests for github_integration.py."""

import json
import pytest
import importlib
from unittest.mock import Mock, MagicMock, patch, mock_open

github_module = importlib.import_module('any-llm-code-review.github_integration')
models_module = importlib.import_module('any-llm-code-review.models')

GitHubReviewPoster = github_module.GitHubReviewPoster
CodeReviewResponse = models_module.CodeReviewResponse
ReviewComment = models_module.ReviewComment


@pytest.fixture
def mock_github():
    """Mock GitHub API objects."""
    with patch.object(github_module, 'Github') as mock_gh:
        mock_repo = Mock()
        mock_pr = Mock()
        mock_pr.title = "Test PR"
        mock_pr.body = "Test PR description"

        mock_gh.return_value.get_repo.return_value = mock_repo
        mock_repo.get_pull.return_value = mock_pr

        yield {
            'github': mock_gh,
            'repo': mock_repo,
            'pr': mock_pr
        }


class TestGitHubReviewPoster:
    """Tests for GitHubReviewPoster class."""

    def test_init(self, mock_github):
        """Test GitHubReviewPoster initialization."""
        poster = GitHubReviewPoster(
            token="test-token",
            repository="owner/repo",
            pr_number=123
        )

        assert poster.pr_number == 123
        assert poster.review_title == "AI Code Review"
        mock_github['github'].assert_called_once_with("test-token")
        mock_github['github'].return_value.get_repo.assert_called_once_with("owner/repo")
        mock_github['repo'].get_pull.assert_called_once_with(123)

    def test_init_with_custom_title(self, mock_github):
        """Test GitHubReviewPoster initialization with custom review title."""
        poster = GitHubReviewPoster(
            token="test-token",
            repository="owner/repo",
            pr_number=123,
            review_title="Security Review"
        )

        assert poster.review_title == "Security Review"

    def test_get_pr_files(self, mock_github):
        """Test getting PR files and their diffs."""
        mock_file1 = Mock()
        mock_file1.filename = "src/main.py"
        mock_file1.patch = "@@ -1,3 +1,4 @@\n def main():\n+    print('hello')\n     pass"

        mock_file2 = Mock()
        mock_file2.filename = "src/utils.py"
        mock_file2.patch = "@@ -1,2 +1,3 @@\n def util():\n+    return True\n     pass"

        mock_file3 = Mock()
        mock_file3.filename = "image.png"
        mock_file3.patch = None

        mock_github['pr'].get_files.return_value = [mock_file1, mock_file2, mock_file3]

        poster = GitHubReviewPoster(
            token="test-token",
            repository="owner/repo",
            pr_number=123
        )

        file_diffs = poster.get_pr_files()

        assert len(file_diffs) == 2
        assert "src/main.py" in file_diffs
        assert "src/utils.py" in file_diffs
        assert "image.png" not in file_diffs
        assert "print('hello')" in file_diffs["src/main.py"]

    def test_post_review_approved_no_comments(self, mock_github):
        """Test posting a review that's approved with no comments."""
        poster = GitHubReviewPoster(
            token="test-token",
            repository="owner/repo",
            pr_number=123
        )

        review = CodeReviewResponse(
            summary="Code looks great!",
            comments=[],
            approved=True
        )

        poster.post_review(review)

        mock_github['pr'].create_review.assert_called_once()
        call_args = mock_github['pr'].create_review.call_args
        assert "✅ **APPROVED**" in call_args[1]['body']
        assert "Code looks great!" in call_args[1]['body']
        assert call_args[1]['event'] == "COMMENT"

    def test_post_review_with_comments(self, mock_github):
        """Test posting a review with inline comments."""
        poster = GitHubReviewPoster(
            token="test-token",
            repository="owner/repo",
            pr_number=123
        )

        review = CodeReviewResponse(
            summary="Found some issues",
            comments=[
                ReviewComment(
                    path="src/main.py",
                    line=10,
                    severity="error",
                    category="bug",
                    message="Potential null pointer exception",
                    suggestion="Add null check"
                ),
                ReviewComment(
                    path="src/utils.py",
                    line=5,
                    severity="warning",
                    category="performance",
                    message="This could be optimized"
                )
            ],
            approved=False
        )

        poster.post_review(review)

        mock_github['pr'].create_review.assert_called_once()
        call_args = mock_github['pr'].create_review.call_args

        assert "⚠️ **CHANGES REQUESTED**" in call_args[1]['body']
        assert "Found some issues" in call_args[1]['body']
        assert call_args[1]['event'] == "COMMENT"

        comments = call_args[1]['comments']
        assert len(comments) == 2

        assert comments[0]['path'] == "src/main.py"
        assert comments[0]['line'] == 10
        assert comments[0]['side'] == "RIGHT"
        assert "🚨" in comments[0]['body']
        assert "BUG" in comments[0]['body']
        assert "Potential null pointer exception" in comments[0]['body']
        assert "Add null check" in comments[0]['body']

        assert comments[1]['path'] == "src/utils.py"
        assert comments[1]['line'] == 5
        assert "⚠️" in comments[1]['body']
        assert "PERFORMANCE" in comments[1]['body']

    def test_post_review_severity_emojis(self, mock_github):
        """Test that correct emojis are used for different severity levels."""
        poster = GitHubReviewPoster(
            token="test-token",
            repository="owner/repo",
            pr_number=123
        )

        review = CodeReviewResponse(
            summary="Various issues",
            comments=[
                ReviewComment(
                    path="src/main.py",
                    line=1,
                    severity="error",
                    category="bug",
                    message="Error message"
                ),
                ReviewComment(
                    path="src/main.py",
                    line=2,
                    severity="warning",
                    category="style",
                    message="Warning message"
                ),
                ReviewComment(
                    path="src/main.py",
                    line=3,
                    severity="info",
                    category="suggestion",
                    message="Info message"
                )
            ],
            approved=False
        )

        poster.post_review(review)

        comments = mock_github['pr'].create_review.call_args[1]['comments']

        assert "🚨" in comments[0]['body']
        assert "⚠️" in comments[1]['body']
        assert "💡" in comments[2]['body']

    def test_post_review_fallback_to_issue_comment(self, mock_github):
        """Test fallback to issue comment when review creation fails."""
        poster = GitHubReviewPoster(
            token="test-token",
            repository="owner/repo",
            pr_number=123
        )

        review = CodeReviewResponse(
            summary="Review summary",
            comments=[
                ReviewComment(
                    path="src/main.py",
                    line=10,
                    severity="error",
                    category="bug",
                    message="Error message"
                )
            ],
            approved=False
        )

        mock_github['pr'].create_review.side_effect = Exception("API Error")
        poster.post_review(review)
        mock_github['pr'].create_issue_comment.assert_called_once()
        comment_body = mock_github['pr'].create_issue_comment.call_args[0][0]

        assert "Review summary" in comment_body
        assert "src/main.py:10" in comment_body
        assert "Error message" in comment_body


class TestGitHubReviewPosterFromEnv:
    """Tests for GitHubReviewPoster.from_env() class method."""

    def test_from_env_with_github_ref(self, mock_github, monkeypatch):
        """Test creating poster from environment with GITHUB_REF."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_REF", "refs/pull/456/merge")

        poster = GitHubReviewPoster.from_env()

        assert poster.pr_number == 456

    def test_from_env_with_event_path(self, mock_github, monkeypatch, tmp_path):
        """Test creating poster from environment with event payload."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
        event_file = tmp_path / "event.json"
        event_data = {
            "pull_request": {
                "number": 789
            }
        }
        event_file.write_text(json.dumps(event_data))
        monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))

        poster = GitHubReviewPoster.from_env()

        assert poster.pr_number == 789

    def test_from_env_with_custom_review_title(self, mock_github, monkeypatch):
        """Test creating poster with custom review title from env."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_REF", "refs/pull/123/merge")
        monkeypatch.setenv("REVIEW_TITLE", "Custom Review Title")

        poster = GitHubReviewPoster.from_env()

        assert poster.review_title == "Custom Review Title"

    def test_from_env_missing_pr_number(self, mock_github, monkeypatch):
        """Test that missing PR number raises error."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
        monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

        with pytest.raises(ValueError, match="Could not determine PR number"):
            GitHubReviewPoster.from_env()

    def test_from_env_default_review_title(self, mock_github, monkeypatch):
        """Test default review title when not specified."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_REF", "refs/pull/123/merge")
        monkeypatch.delenv("REVIEW_TITLE", raising=False)

        poster = GitHubReviewPoster.from_env()

        assert poster.review_title == "AI Code Review"
