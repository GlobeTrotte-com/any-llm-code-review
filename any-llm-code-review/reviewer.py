"""Core AI code reviewer using pydantic-ai."""

import fnmatch
import os
from pydantic_ai import Agent
from pydantic_ai.output import PromptedOutput

from .config import ReviewConfig
from .models import CodeReviewResponse


SYSTEM_PROMPT = """You are an expert code reviewer. Your role is to:

1. Analyze code changes for:
   - Bugs and logic errors
   - Security vulnerabilities
   - Performance issues
   - Code quality and best practices
   - Potential edge cases
   - Maintainability concerns

2. Provide constructive feedback:
   - Be specific and actionable
   - Suggest improvements when appropriate
   - Explain the reasoning behind your comments
   - Categorize issues appropriately

3. Severity levels:
   - error: Critical issues that must be fixed (bugs, security issues)
   - warning: Important issues that should be addressed (performance, best practices)
   - info: Suggestions and minor improvements

4. Line numbers - CRITICAL:
   Each diff line is annotated with [Line X] showing its exact line number in the new file.

   Example:
   ```diff
   @@ -76,14 +76,15 @@
   [Line 76]  @classmethod
   [Line 77]  def from_env(cls) -> "ReviewConfig":
   [Line 78]      \"\"\"Create config from environment variables.\"\"\"
   [Line 79]      return cls(
   [Line 80]          model_provider=os.getenv("MODEL_PROVIDER", "openai"),
   [Line 81]          model_name=os.getenv("MODEL_NAME", "gpt-4"),
   [Line 82]          api_key=os.getenv("API_KEY"),
   [Line 83]          base_url=os.getenv("BASE_URL"),
   [Line 84]          max_tokens=int(os.getenv("MAX_TOKENS", "4000")),
   [Line 85]          temperature=float(os.getenv("TEMPERATURE", "0.3")),
   [Line 86]          github_token=os.getenv("GITHUB_TOKEN", ""),
   [Line 87] +        ignore_patterns=os.getenv("IGNORE_PATTERNS").split(",") if os.getenv("IGNORE_PATTERNS") else [
   [Line 88] +            "*.md",
   ```

   TO COMMENT ON A LINE:
   - Look for the [Line X] annotation at the start of the line
   - Use that EXACT number in your comment's "line" field
   - Example: To comment on the ignore_patterns issue above, use line: 87

   DO NOT try to calculate line numbers yourself - just read the [Line X] annotations!

Only report genuine issues. If the code looks good, approve it with an empty comments list.
"""


class CodeReviewer:
    """AI-powered code reviewer supporting multiple model providers."""

    def __init__(self, config: ReviewConfig):
        """Initialize the code reviewer with configuration."""
        self.config = config
        self.model = self._create_model()

        # Use PromptedOutput for HuggingFace models that may not support tool calling
        # This uses prompt engineering + JSON mode instead of tool calls
        if self.config.model_provider == "huggingface":
            output_type = PromptedOutput(
                CodeReviewResponse,
                name="code_review",
                description="Structured code review with categorized feedback"
            )
        else:
            # Use default tool-based output for other providers
            output_type = CodeReviewResponse

        # Use custom prompt if provided, otherwise use default
        system_prompt = self.config.custom_prompt or SYSTEM_PROMPT

        self.agent = Agent(
            self.model,
            output_type=output_type,
            system_prompt=system_prompt,
        )

    def _create_model(self) -> str:
        """Create the appropriate model string based on provider configuration."""
        provider = self.config.model_provider
        model_name = self.config.model_name

        # Set environment variables for API keys if provided
        # pydantic-ai reads API keys from environment variables
        if self.config.api_key:
            if provider == "openai":
                os.environ["OPENAI_API_KEY"] = self.config.api_key
            elif provider == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = self.config.api_key
            elif provider == "gemini":
                os.environ["GEMINI_API_KEY"] = self.config.api_key
            elif provider == "groq":
                os.environ["GROQ_API_KEY"] = self.config.api_key
            elif provider == "mistral":
                os.environ["MISTRAL_API_KEY"] = self.config.api_key
            elif provider == "huggingface":
                os.environ["HF_TOKEN"] = self.config.api_key

        # For base_url (Ollama or custom endpoints)
        if self.config.base_url:
            if provider == "openai":
                os.environ["OPENAI_BASE_URL"] = self.config.base_url
            elif provider == "ollama":
                os.environ["OLLAMA_BASE_URL"] = self.config.base_url

        if provider == "gemini":
            # Gemini infers from model name automatically
            return model_name
        elif provider == "huggingface":
            # Hugging Face uses huggingface: prefix
            return f"huggingface:{model_name}"
        elif provider == "ollama":
            return f"ollama:{model_name}"
        elif provider == "openai":
            return f"openai:{model_name}"
        elif provider == "anthropic":
            return f"anthropic:{model_name}"
        elif provider == "groq":
            return f"groq:{model_name}"
        elif provider == "mistral":
            return f"mistral:{model_name}"
        else:
            # Generic fallback - try with prefix
            return f"{provider}:{model_name}"

    def should_ignore_file(self, file_path: str) -> bool:
        """Check if file should be ignored based on patterns."""
        for pattern in self.config.ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def annotate_diff_with_line_numbers(self, diff: str) -> str:
        """
        Annotate a diff with explicit line numbers to help AI accuracy.

        Transforms:
        ```diff
        @@ -76,14 +76,15 @@
         @classmethod
        +        ignore_patterns=...
        ```

        Into:
        ```diff
        @@ -76,14 +76,15 @@
        [Line 76]  @classmethod
        [Line 87] +        ignore_patterns=...
        ```
        """
        lines = diff.split('\n')
        result = []
        current_line = None

        for line in lines:
            # Check for diff header to reset line counter
            if line.startswith('@@'):
                result.append(line)
                # Extract the new file starting line number
                # Format: @@ -old_start,old_count +new_start,new_count @@
                parts = line.split('+')
                if len(parts) >= 2:
                    new_start = parts[1].split(',')[0].split()[0]
                    try:
                        current_line = int(new_start)
                    except ValueError:
                        current_line = None
                continue

            if current_line is None:
                # Before any @@ header, just pass through
                result.append(line)
                continue

            # Lines starting with '-' are deletions (don't count)
            if line.startswith('-'):
                result.append(line)
            # Lines starting with '+' are additions (count them)
            elif line.startswith('+'):
                result.append(f"[Line {current_line}] {line}")
                current_line += 1
            # Lines starting with ' ' (space) are context (count them)
            elif line.startswith(' '):
                result.append(f"[Line {current_line}] {line}")
                current_line += 1
            else:
                # Empty lines or other content
                result.append(line)

        return '\n'.join(result)

    async def review_changes(
        self,
        file_changes: dict[str, str],
        pr_title: str = "",
        pr_description: str = "",
    ) -> CodeReviewResponse:
        """
        Review code changes and return structured feedback.

        Args:
            file_changes: Dict mapping file paths to their diff content
            pr_title: Optional PR title for context
            pr_description: Optional PR description for context

        Returns:
            CodeReviewResponse with summary and comments
        """
        # Filter out ignored files and large files
        filtered_changes = {}
        for path, diff in file_changes.items():
            if self.should_ignore_file(path):
                continue
            if len(diff) > self.config.max_file_size:
                continue
            filtered_changes[path] = diff

        if not filtered_changes:
            return CodeReviewResponse(
                summary="No files to review (all files filtered out).",
                comments=[],
                approved=True,
            )

        # Build the review prompt
        prompt_parts = []

        if pr_title:
            prompt_parts.append(f"PR Title: {pr_title}")
        if pr_description:
            prompt_parts.append(f"PR Description: {pr_description}")

        prompt_parts.append("\n## Code Changes\n")

        for path, diff in filtered_changes.items():
            prompt_parts.append(f"\n### File: {path}\n")
            prompt_parts.append("```diff")
            # Annotate diff with explicit line numbers for accuracy
            annotated_diff = self.annotate_diff_with_line_numbers(diff)
            prompt_parts.append(annotated_diff)
            prompt_parts.append("```\n")

        prompt = "\n".join(prompt_parts)

        # Run the AI review
        result = await self.agent.run(prompt)

        return result.output
