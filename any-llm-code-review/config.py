"""Configuration for AI code reviewer."""

import os
from typing import Literal, Optional
from pydantic import BaseModel, Field


ModelProvider = Literal[
    "openai",
    "anthropic",
    "gemini",
    "groq",
    "mistral",
    "cohere",
    "bedrock",
    "vertexai",
    "ollama",
    "huggingface",
]


class ReviewConfig(BaseModel):
    """Configuration for code review."""

    model_provider: ModelProvider = Field(
        description="AI model provider to use"
    )
    model_name: str = Field(
        description="Specific model name (e.g., 'gpt-4', 'claude-3-5-sonnet-20241022', 'gemini-1.5-pro')"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for the model provider (not needed for Ollama)"
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Optional base URL for API (useful for Ollama or custom endpoints)"
    )
    max_tokens: int = Field(
        default=4000,
        description="Maximum tokens for the response"
    )
    temperature: float = Field(
        default=0.3,
        description="Temperature for model responses (0.0-1.0)"
    )
    github_token: str = Field(
        description="GitHub token for API access"
    )
    ignore_patterns: list[str] = Field(
        default_factory=lambda: [
            "*.md",
            "*.txt",
            "*.json",
            "*.yaml",
            "*.yml",
            "package-lock.json",
            "yarn.lock",
            "poetry.lock",
        ],
        description="File patterns to ignore during review"
    )
    max_file_size: int = Field(
        default=10000,
        description="Maximum file size in characters to review"
    )
    custom_prompt: Optional[str] = Field(
        default=None,
        description="Custom system prompt for the code reviewer (overrides default)"
    )
    review_title: str = Field(
        default="AI Code Review",
        description="Title for the code review comment"
    )

    @classmethod
    def from_env(cls) -> "ReviewConfig":
        """Create config from environment variables."""
        return cls(
            model_provider=os.getenv("MODEL_PROVIDER", "openai"),
            model_name=os.getenv("MODEL_NAME", "gpt-4"),
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
            max_tokens=int(os.getenv("MAX_TOKENS", "4000")),
            temperature=float(os.getenv("TEMPERATURE", "0.3")),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            ignore_patterns=os.getenv("IGNORE_PATTERNS", "").split(",") if os.getenv("IGNORE_PATTERNS") else [
                "*.md",
                "*.txt",
                "*.json",
                "*.yaml",
                "*.yml",
                "package-lock.json",
                "yarn.lock",
                "poetry.lock",
            ],
            max_file_size=int(os.getenv("MAX_FILE_SIZE", "10000")),
            custom_prompt=os.getenv("CUSTOM_PROMPT"),
            review_title=os.getenv("REVIEW_TITLE", "AI Code Review"),
        )
