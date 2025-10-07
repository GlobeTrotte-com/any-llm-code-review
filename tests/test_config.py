"""Tests for config.py."""

import pytest
import importlib
from pydantic import ValidationError

config_module = importlib.import_module('any-llm-code-review.config')
ReviewConfig = config_module.ReviewConfig


class TestReviewConfig:
    """Tests for ReviewConfig model."""

    def test_create_config_with_minimal_fields(self):
        """Test creating a ReviewConfig with minimal required fields."""
        config = ReviewConfig(
            model_provider="openai",
            model_name="gpt-4",
            github_token="test-token"
        )

        assert config.model_provider == "openai"
        assert config.model_name == "gpt-4"
        assert config.github_token == "test-token"
        assert config.api_key is None
        assert config.max_tokens == 4000
        assert config.temperature == 0.3

    def test_create_config_with_all_fields(self, sample_review_config):
        """Test creating a ReviewConfig with all fields."""
        assert sample_review_config.model_provider == "openai"
        assert sample_review_config.model_name == "gpt-4"
        assert sample_review_config.api_key == "test-api-key"
        assert sample_review_config.github_token == "test-github-token"
        assert sample_review_config.max_tokens == 4000
        assert sample_review_config.temperature == 0.3

    def test_default_ignore_patterns(self):
        """Test that default ignore patterns are set correctly."""
        config = ReviewConfig(
            model_provider="openai",
            model_name="gpt-4",
            github_token="test-token"
        )

        assert "*.md" in config.ignore_patterns
        assert "*.json" in config.ignore_patterns
        assert "package-lock.json" in config.ignore_patterns
        assert "yarn.lock" in config.ignore_patterns

    def test_custom_ignore_patterns(self):
        """Test setting custom ignore patterns."""
        config = ReviewConfig(
            model_provider="openai",
            model_name="gpt-4",
            github_token="test-token",
            ignore_patterns=["*.txt", "*.log"]
        )

        assert config.ignore_patterns == ["*.txt", "*.log"]

    def test_custom_prompt(self):
        """Test setting a custom prompt."""
        custom_prompt = "You are a security-focused code reviewer."
        config = ReviewConfig(
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            github_token="test-token",
            custom_prompt=custom_prompt
        )

        assert config.custom_prompt == custom_prompt

    def test_review_title(self):
        """Test setting a custom review title."""
        config = ReviewConfig(
            model_provider="openai",
            model_name="gpt-4",
            github_token="test-token",
            review_title="Security Review"
        )

        assert config.review_title == "Security Review"

    def test_default_review_title(self):
        """Test default review title."""
        config = ReviewConfig(
            model_provider="openai",
            model_name="gpt-4",
            github_token="test-token"
        )

        assert config.review_title == "AI Code Review"

    def test_invalid_model_provider(self):
        """Test that invalid model provider raises ValidationError."""
        with pytest.raises(ValidationError):
            ReviewConfig(
                model_provider="invalid-provider",
                model_name="gpt-4",
                github_token="test-token"
            )

    def test_valid_model_providers(self):
        """Test all valid model providers."""
        providers = [
            "openai", "anthropic", "gemini", "groq", "mistral",
            "cohere", "bedrock", "vertexai", "ollama", "huggingface"
        ]

        for provider in providers:
            config = ReviewConfig(
                model_provider=provider,
                model_name="test-model",
                github_token="test-token"
            )
            assert config.model_provider == provider

    def test_temperature_range(self):
        """Test that temperature can be set within valid range."""
        config = ReviewConfig(
            model_provider="openai",
            model_name="gpt-4",
            github_token="test-token",
            temperature=0.5
        )

        assert config.temperature == 0.5

    def test_max_file_size(self):
        """Test setting max file size."""
        config = ReviewConfig(
            model_provider="openai",
            model_name="gpt-4",
            github_token="test-token",
            max_file_size=20000
        )

        assert config.max_file_size == 20000


class TestReviewConfigFromEnv:
    """Tests for ReviewConfig.from_env() class method."""

    def test_from_env_with_all_variables(self, monkeypatch):
        """Test creating config from environment variables with all vars set."""
        monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
        monkeypatch.setenv("MODEL_NAME", "claude-3-5-sonnet-20241022")
        monkeypatch.setenv("API_KEY", "test-api-key")
        monkeypatch.setenv("BASE_URL", "https://api.example.com")
        monkeypatch.setenv("MAX_TOKENS", "8000")
        monkeypatch.setenv("TEMPERATURE", "0.5")
        monkeypatch.setenv("GITHUB_TOKEN", "github-token")
        monkeypatch.setenv("IGNORE_PATTERNS", "*.txt,*.log")
        monkeypatch.setenv("MAX_FILE_SIZE", "15000")
        monkeypatch.setenv("CUSTOM_PROMPT", "Custom prompt text")
        monkeypatch.setenv("REVIEW_TITLE", "Security Review")

        config = ReviewConfig.from_env()

        assert config.model_provider == "anthropic"
        assert config.model_name == "claude-3-5-sonnet-20241022"
        assert config.api_key == "test-api-key"
        assert config.base_url == "https://api.example.com"
        assert config.max_tokens == 8000
        assert config.temperature == 0.5
        assert config.github_token == "github-token"
        assert config.ignore_patterns == ["*.txt", "*.log"]
        assert config.max_file_size == 15000
        assert config.custom_prompt == "Custom prompt text"
        assert config.review_title == "Security Review"

    def test_from_env_with_defaults(self, monkeypatch):
        """Test creating config from environment with default values."""
        monkeypatch.delenv("MODEL_PROVIDER", raising=False)
        monkeypatch.delenv("MODEL_NAME", raising=False)
        monkeypatch.delenv("IGNORE_PATTERNS", raising=False)

        config = ReviewConfig.from_env()

        assert config.model_provider == "openai"
        assert config.model_name == "gpt-4"
        assert config.max_tokens == 4000
        assert config.temperature == 0.3
        assert "*.md" in config.ignore_patterns
        assert config.max_file_size == 10000
        assert config.review_title == "AI Code Review"

    def test_from_env_empty_ignore_patterns(self, monkeypatch):
        """Test that empty IGNORE_PATTERNS uses defaults."""
        monkeypatch.setenv("IGNORE_PATTERNS", "")

        config = ReviewConfig.from_env()

        assert "*.md" in config.ignore_patterns
        assert "*.json" in config.ignore_patterns

    def test_from_env_with_ignore_patterns_set(self, monkeypatch):
        """Test that IGNORE_PATTERNS overrides defaults when set."""
        monkeypatch.setenv("IGNORE_PATTERNS", "*.py,*.js")

        config = ReviewConfig.from_env()

        assert config.ignore_patterns == ["*.py", "*.js"]
        assert "*.md" not in config.ignore_patterns
