"""Tests for main.py CLI and integration."""

import pytest
import importlib
from unittest.mock import Mock, AsyncMock, patch
from click.testing import CliRunner

main_module = importlib.import_module('any-llm-code-review.main')
models_module = importlib.import_module('any-llm-code-review.models')

cli = main_module.cli
review_pr = main_module.review_pr
review_pr_from_env = main_module.review_pr_from_env
CodeReviewResponse = models_module.CodeReviewResponse
ReviewComment = models_module.ReviewComment


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_review_components():
    """Mock the main components for review."""
    with patch.object(main_module, 'CodeReviewer') as mock_reviewer, \
         patch.object(main_module, 'GitHubReviewPoster') as mock_poster:

        mock_reviewer_instance = Mock()
        mock_reviewer.return_value = mock_reviewer_instance

        mock_poster_instance = Mock()
        mock_poster_instance.pr.title = "Test PR"
        mock_poster_instance.pr.body = "Test description"
        mock_poster_instance.get_pr_files.return_value = {
            "src/test.py": "@@ -1,1 +1,2 @@\n def test():\n+    pass"
        }
        mock_poster.return_value = mock_poster_instance

        mock_review_result = CodeReviewResponse(
            summary="Code looks good",
            comments=[],
            approved=True
        )
        mock_reviewer_instance.review_changes = AsyncMock(return_value=mock_review_result)

        yield {
            'reviewer_class': mock_reviewer,
            'reviewer_instance': mock_reviewer_instance,
            'poster_class': mock_poster,
            'poster_instance': mock_poster_instance,
            'review_result': mock_review_result
        }


class TestCLI:
    """Tests for CLI commands."""

    def test_cli_group_exists(self, cli_runner):
        """Test that CLI group is accessible."""
        result = cli_runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "AI Code Reviewer" in result.output

    def test_review_command_exists(self, cli_runner):
        """Test that review command exists and shows help."""
        result = cli_runner.invoke(cli, ['review', '--help'])
        assert result.exit_code == 0
        assert "--provider" in result.output
        assert "--model" in result.output
        assert "--github-token" in result.output

    def test_review_from_env_command_exists(self, cli_runner):
        """Test that review-from-env command exists."""
        result = cli_runner.invoke(cli, ['review-from-env', '--help'])
        assert result.exit_code == 0


class TestReviewCommand:
    """Tests for the review command."""

    def test_review_command_with_all_options(self, cli_runner, mock_review_components):
        """Test review command with all options."""
        result = cli_runner.invoke(cli, [
            'review',
            '--provider', 'openai',
            '--model', 'gpt-4',
            '--api-key', 'test-key',
            '--github-token', 'gh-token',
            '--repository', 'owner/repo',
            '--pr-number', '123',
            '--max-tokens', '8000',
            '--temperature', '0.5',
            '--custom-prompt', 'Custom prompt',
            '--review-title', 'Custom Title'
        ])

        assert result.exit_code == 0
        assert "Code looks good" in result.output
        assert "Total comments: 0" in result.output
        assert "Approved: True" in result.output

    def test_review_command_missing_required_options(self, cli_runner):
        """Test that review command requires necessary options."""
        result = cli_runner.invoke(cli, ['review'])

        assert result.exit_code != 0
        assert "Error" in result.output or "Missing option" in result.output

    def test_review_command_with_minimal_options(self, cli_runner, mock_review_components):
        """Test review command with minimal required options."""
        result = cli_runner.invoke(cli, [
            'review',
            '--provider', 'openai',
            '--model', 'gpt-4',
            '--github-token', 'gh-token',
            '--repository', 'owner/repo',
            '--pr-number', '123'
        ])

        assert result.exit_code == 0


class TestReviewPRFunction:
    """Tests for the review_pr async function."""

    @pytest.mark.asyncio
    async def test_review_pr_success(self, mock_review_components):
        """Test successful PR review flow."""
        with pytest.raises(SystemExit) as exc_info:
            await review_pr(
                provider="openai",
                model="gpt-4",
                api_key="test-key",
                github_token="gh-token",
                repository="owner/repo",
                pr_number=123
            )

        assert exc_info.value.code == 0
        mock_review_components['reviewer_class'].assert_called_once()
        mock_review_components['poster_class'].assert_called_once()
        mock_review_components['reviewer_instance'].review_changes.assert_called_once()
        mock_review_components['poster_instance'].post_review.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_pr_with_custom_options(self, mock_review_components):
        """Test PR review with custom options."""
        with pytest.raises(SystemExit) as exc_info:
            await review_pr(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                api_key="test-key",
                github_token="gh-token",
                repository="owner/repo",
                pr_number=456,
                base_url="https://custom.api.com",
                max_tokens=8000,
                temperature=0.5,
                custom_prompt="Custom security review",
                review_title="Security Review"
            )

        assert exc_info.value.code == 0
        call_args = mock_review_components['reviewer_class'].call_args[0][0]
        assert call_args.model_provider == "anthropic"
        assert call_args.model_name == "claude-3-5-sonnet-20241022"
        assert call_args.base_url == "https://custom.api.com"
        assert call_args.max_tokens == 8000
        assert call_args.temperature == 0.5
        assert call_args.custom_prompt == "Custom security review"

    @pytest.mark.asyncio
    async def test_review_pr_with_comments(self, mock_review_components):
        """Test PR review with comments in the result."""
        review_with_comments = CodeReviewResponse(
            summary="Found some issues",
            comments=[
                ReviewComment(
                    path="src/test.py",
                    line=10,
                    severity="error",
                    category="bug",
                    message="Bug found"
                ),
                ReviewComment(
                    path="src/test.py",
                    line=20,
                    severity="warning",
                    category="style",
                    message="Style issue"
                )
            ],
            approved=False
        )
        mock_review_components['reviewer_instance'].review_changes = AsyncMock(
            return_value=review_with_comments
        )

        with pytest.raises(SystemExit) as exc_info:
            await review_pr(
                provider="openai",
                model="gpt-4",
                api_key="test-key",
                github_token="gh-token",
                repository="owner/repo",
                pr_number=123
            )

        assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_review_pr_handles_exceptions(self, mock_review_components):
        """Test that exceptions are handled properly."""
        mock_review_components['poster_instance'].get_pr_files.side_effect = Exception("API Error")

        with pytest.raises(SystemExit) as exc_info:
            await review_pr(
                provider="openai",
                model="gpt-4",
                api_key="test-key",
                github_token="gh-token",
                repository="owner/repo",
                pr_number=123
            )

        assert exc_info.value.code == 1


class TestReviewPRFromEnv:
    """Tests for review_pr_from_env function."""

    @pytest.mark.asyncio
    async def test_review_pr_from_env_success(self, mock_review_components, monkeypatch):
        """Test successful review from environment variables."""
        monkeypatch.setenv("MODEL_PROVIDER", "openai")
        monkeypatch.setenv("MODEL_NAME", "gpt-4")
        monkeypatch.setenv("GITHUB_TOKEN", "gh-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_REF", "refs/pull/123/merge")

        with patch.object(main_module, 'ReviewConfig') as mock_config, \
             patch.object(main_module, 'GitHubReviewPoster') as mock_poster:

            mock_config.from_env.return_value = Mock()
            mock_poster_instance = Mock()
            mock_poster_instance.pr.title = "Test PR"
            mock_poster_instance.pr.body = "Description"
            mock_poster_instance.get_pr_files.return_value = {"test.py": "diff"}
            mock_poster.from_env.return_value = mock_poster_instance

            mock_reviewer = Mock()
            mock_reviewer.review_changes = AsyncMock(return_value=CodeReviewResponse(
                summary="Good",
                comments=[],
                approved=True
            ))

            with patch.object(main_module, 'CodeReviewer', return_value=mock_reviewer):
                with pytest.raises(SystemExit) as exc_info:
                    await review_pr_from_env()

                assert exc_info.value.code == 0

    @pytest.mark.asyncio
    async def test_review_pr_from_env_handles_errors(self, monkeypatch):
        """Test that errors are handled in review_pr_from_env."""
        with patch.object(main_module, 'ReviewConfig') as mock_config:
            mock_config.from_env.side_effect = Exception("Config error")

            with pytest.raises(SystemExit) as exc_info:
                await review_pr_from_env()

            assert exc_info.value.code == 1
