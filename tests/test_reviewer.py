"""Tests for reviewer.py."""

import pytest
import importlib
from unittest.mock import Mock, AsyncMock, patch

reviewer_module = importlib.import_module('any-llm-code-review.reviewer')
config_module = importlib.import_module('any-llm-code-review.config')
models_module = importlib.import_module('any-llm-code-review.models')

CodeReviewer = reviewer_module.CodeReviewer
ReviewConfig = config_module.ReviewConfig
CodeReviewResponse = models_module.CodeReviewResponse
ReviewComment = models_module.ReviewComment


class TestCodeReviewer:
    """Tests for CodeReviewer class."""

    def test_init_creates_model(self, sample_review_config):
        """Test that CodeReviewer initializes with config."""
        reviewer = CodeReviewer(sample_review_config)

        assert reviewer.config == sample_review_config
        assert reviewer.model is not None
        assert reviewer.agent is not None

    def test_create_model_openai(self):
        """Test creating OpenAI model string."""
        config = ReviewConfig(
            model_provider="openai",
            model_name="gpt-4",
            github_token="test-token",
            api_key="test-key"
        )
        reviewer = CodeReviewer(config)

        assert reviewer.model == "openai:gpt-4"

    def test_create_model_anthropic(self):
        """Test creating Anthropic model string."""
        config = ReviewConfig(
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            github_token="test-token",
            api_key="test-key"
        )
        reviewer = CodeReviewer(config)

        assert reviewer.model == "anthropic:claude-3-5-sonnet-20241022"

    def test_create_model_gemini(self):
        """Test creating Gemini model string."""
        config = ReviewConfig(
            model_provider="gemini",
            model_name="gemini-2.0-pro",
            github_token="test-token",
            api_key="test-key"
        )
        reviewer = CodeReviewer(config)

        assert reviewer.model == "google-gla:gemini-2.0-pro"

    @pytest.mark.skip(reason="Ollama model requires local Ollama installation")
    def test_create_model_ollama(self):
        """Test creating Ollama model string."""
        config = ReviewConfig(
            model_provider="ollama",
            model_name="llama3.1",
            github_token="test-token",
            base_url="http://localhost:11434"
        )
        reviewer = CodeReviewer(config)

        assert reviewer.model == "ollama:llama3.1"

    def test_create_model_huggingface(self):
        """Test creating HuggingFace model string."""
        config = ReviewConfig(
            model_provider="huggingface",
            model_name="Qwen/Qwen2.5-72B-Instruct",
            github_token="test-token",
            api_key="test-key"
        )
        reviewer = CodeReviewer(config)

        assert reviewer.model == "huggingface:Qwen/Qwen2.5-72B-Instruct"

    def test_custom_prompt_usage(self):
        """Test that custom prompt is used when provided."""
        custom_prompt = "You are a security-focused reviewer."
        config = ReviewConfig(
            model_provider="openai",
            model_name="gpt-4",
            github_token="test-token",
            custom_prompt=custom_prompt
        )
        reviewer = CodeReviewer(config)
        assert reviewer.config.custom_prompt == custom_prompt
        assert reviewer.agent is not None

    def test_should_ignore_file_with_matching_pattern(self, sample_review_config):
        """Test file filtering with ignore patterns."""
        reviewer = CodeReviewer(sample_review_config)

        assert reviewer.should_ignore_file("README.md") is True
        assert reviewer.should_ignore_file("config.json") is True
        assert reviewer.should_ignore_file("package-lock.json") is True

    def test_should_not_ignore_file_without_matching_pattern(self, sample_review_config):
        """Test that non-matching files are not ignored."""
        reviewer = CodeReviewer(sample_review_config)

        assert reviewer.should_ignore_file("src/main.py") is False
        assert reviewer.should_ignore_file("lib/utils.js") is False

    def test_should_ignore_file_custom_patterns(self):
        """Test file filtering with custom patterns."""
        config = ReviewConfig(
            model_provider="openai",
            model_name="gpt-4",
            github_token="test-token",
            ignore_patterns=["*.py", "test_*"]
        )
        reviewer = CodeReviewer(config)

        assert reviewer.should_ignore_file("main.py") is True
        assert reviewer.should_ignore_file("test_something.js") is True
        assert reviewer.should_ignore_file("utils.js") is False


class TestDiffAnnotation:
    """Tests for diff annotation with line numbers."""

    def test_annotate_diff_with_line_numbers(self, sample_review_config):
        """Test that diffs are annotated with line numbers correctly."""
        reviewer = CodeReviewer(sample_review_config)

        diff = """@@ -1,5 +1,6 @@
 def calculate_total(items):
     total = 0
     for item in items:
         total += item.price
+    print(f"Total: {total}")
     return total
"""

        annotated = reviewer.annotate_diff_with_line_numbers(diff)

        assert "[Line 1] " in annotated
        assert "[Line 5] +" in annotated
        assert "print(f\"Total: {total}\")" in annotated
        assert "[Line 6]  " in annotated
        assert "return total" in annotated

    def test_annotate_diff_with_multiple_hunks(self, sample_review_config):
        """Test annotation with multiple diff hunks."""
        reviewer = CodeReviewer(sample_review_config)

        diff = """@@ -10,3 +10,4 @@
 def func1():
     return 1
+    # New comment

@@ -20,2 +21,3 @@
 def func2():
+    print("hello")
     return 2
"""

        annotated = reviewer.annotate_diff_with_line_numbers(diff)
        assert "[Line 10] " in annotated
        assert "[Line 12] +" in annotated
        assert "[Line 21] " in annotated
        assert "[Line 22] +" in annotated

    def test_annotate_diff_handles_deletions(self, sample_review_config):
        """Test that deletions are not numbered."""
        reviewer = CodeReviewer(sample_review_config)

        diff = """@@ -5,4 +5,3 @@
 def example():
-    old_code = True
     new_code = True
     return new_code
"""

        annotated = reviewer.annotate_diff_with_line_numbers(diff)
        assert "-    old_code = True" in annotated
        assert "[Line" not in annotated.split("\n")[2]  # The deletion line
        assert "[Line 6] " in annotated


class TestReviewChanges:
    """Tests for review_changes method."""

    @pytest.mark.asyncio
    async def test_review_changes_filters_ignored_files(self, sample_review_config):
        """Test that ignored files are filtered out."""
        reviewer = CodeReviewer(sample_review_config)

        file_changes = {
            "README.md": "@@ -1,1 +1,2 @@\n # Title\n+Added line",
            "src/main.py": "@@ -1,1 +1,2 @@\n def main():\n+    pass"
        }

        with patch.object(reviewer.agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = Mock(output=CodeReviewResponse(
                summary="Looks good",
                comments=[],
                approved=True
            ))
            await reviewer.review_changes(file_changes)
            call_args = mock_run.call_args[0][0]
            assert "README.md" not in call_args
            assert "src/main.py" in call_args

    @pytest.mark.asyncio
    async def test_review_changes_filters_large_files(self, sample_review_config):
        """Test that files exceeding max_file_size are filtered out."""
        reviewer = CodeReviewer(sample_review_config)

        large_diff = "+" + ("x" * 20000)

        file_changes = {
            "large.py": large_diff,
            "small.py": "@@ -1,1 +1,2 @@\n def small():\n+    pass"
        }

        with patch.object(reviewer.agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = Mock(output=CodeReviewResponse(
                summary="Looks good",
                comments=[],
                approved=True
            ))
            await reviewer.review_changes(file_changes)
            call_args = mock_run.call_args[0][0]
            assert "large.py" not in call_args
            assert "small.py" in call_args

    @pytest.mark.asyncio
    async def test_review_changes_includes_pr_context(self, sample_review_config):
        """Test that PR title and description are included in prompt."""
        reviewer = CodeReviewer(sample_review_config)

        file_changes = {
            "src/main.py": "@@ -1,1 +1,2 @@\n def main():\n+    pass"
        }

        with patch.object(reviewer.agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = Mock(output=CodeReviewResponse(
                summary="Looks good",
                comments=[],
                approved=True
            ))

            await reviewer.review_changes(
                file_changes,
                pr_title="Add new feature",
                pr_description="This PR adds a new feature to improve performance"
            )

            call_args = mock_run.call_args[0][0]
            assert "PR Title: Add new feature" in call_args
            assert "PR Description: This PR adds a new feature to improve performance" in call_args

    @pytest.mark.asyncio
    async def test_review_changes_returns_response(self, sample_review_config):
        """Test that review_changes returns the AI response."""
        reviewer = CodeReviewer(sample_review_config)

        file_changes = {
            "src/main.py": "@@ -1,1 +1,2 @@\n def main():\n+    pass"
        }

        expected_response = CodeReviewResponse(
            summary="Code looks good",
            comments=[],
            approved=True
        )

        with patch.object(reviewer.agent, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = Mock(output=expected_response)

            result = await reviewer.review_changes(file_changes)

            assert result == expected_response

    @pytest.mark.asyncio
    async def test_review_changes_no_files_after_filtering(self, sample_review_config):
        """Test behavior when all files are filtered out."""
        reviewer = CodeReviewer(sample_review_config)

        file_changes = {
            "README.md": "@@ -1,1 +1,2 @@\n # Title\n+Added line",
            "config.json": "@@ -1,1 +1,2 @@\n {}\n+{\"key\": \"value\"}"
        }

        result = await reviewer.review_changes(file_changes)

        assert result.summary == "No files to review (all files filtered out)."
        assert result.comments == []
        assert result.approved is True
