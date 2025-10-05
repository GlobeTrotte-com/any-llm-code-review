"""Main entry point for AI code reviewer."""

import asyncio
import sys
import click
from .config import ReviewConfig
from .reviewer import CodeReviewer
from .github_integration import GitHubReviewPoster


@click.group()
def cli():
    """AI Code Reviewer - Model-agnostic code review using pydantic-ai."""
    pass


@cli.command()
@click.option("--provider", required=True, help="Model provider (openai, anthropic, gemini, etc.)")
@click.option("--model", required=True, help="Model name (e.g., gpt-4, claude-3-5-sonnet-20241022)")
@click.option("--api-key", help="API key for the model provider")
@click.option("--github-token", required=True, help="GitHub token")
@click.option("--repository", required=True, help="Repository (owner/repo)")
@click.option("--pr-number", required=True, type=int, help="Pull request number")
@click.option("--base-url", help="Optional base URL for API")
@click.option("--max-tokens", default=4000, help="Max tokens for response")
@click.option("--temperature", default=0.3, help="Model temperature")
@click.option("--custom-prompt", help="Custom system prompt for review")
@click.option("--review-title", default="AI Code Review", help="Title for the review comment")
def review(
    provider: str,
    model: str,
    api_key: str,
    github_token: str,
    repository: str,
    pr_number: int,
    base_url: str,
    max_tokens: int,
    temperature: float,
    custom_prompt: str,
    review_title: str,
):
    """Review a pull request."""
    asyncio.run(
        review_pr(
            provider,
            model,
            api_key,
            github_token,
            repository,
            pr_number,
            base_url,
            max_tokens,
            temperature,
            custom_prompt,
            review_title,
        )
    )


@cli.command()
def review_from_env():
    """Review a pull request using environment variables."""
    asyncio.run(review_pr_from_env())


async def review_pr(
    provider: str,
    model: str,
    api_key: str,
    github_token: str,
    repository: str,
    pr_number: int,
    base_url: str = None,
    max_tokens: int = 4000,
    temperature: float = 0.3,
    custom_prompt: str = None,
    review_title: str = "AI Code Review",
):
    """Core review logic."""
    try:
        # Create config
        config = ReviewConfig(
            model_provider=provider,
            model_name=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
            github_token=github_token,
            custom_prompt=custom_prompt,
        )

        # Initialize reviewer
        print(f"Initializing code reviewer with {provider}/{model}...")
        reviewer = CodeReviewer(config)

        # Get PR files
        print(f"Fetching PR #{pr_number} from {repository}...")
        gh_poster = GitHubReviewPoster(github_token, repository, pr_number, review_title)
        file_diffs = gh_poster.get_pr_files()

        print(f"Found {len(file_diffs)} files to review")

        # Get PR details for context
        pr_title = gh_poster.pr.title
        pr_description = gh_poster.pr.body or ""

        # Run review
        print("Running AI code review...")
        review_result = await reviewer.review_changes(
            file_diffs,
            pr_title=pr_title,
            pr_description=pr_description,
        )

        # Post review
        print("Posting review to GitHub...")
        gh_poster.post_review(review_result)

        # Print summary
        print("\n" + "=" * 80)
        print("Review Summary:")
        print("=" * 80)
        print(review_result.summary)
        print(f"\nTotal comments: {len(review_result.comments)}")
        print(f"Approved: {review_result.approved}")

        if review_result.comments:
            print("\nComments by severity:")
            for severity in ["error", "warning", "info"]:
                count = sum(1 for c in review_result.comments if c.severity == severity)
                if count > 0:
                    print(f"  {severity}: {count}")

        sys.exit(0 if review_result.approved else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def review_pr_from_env():
    """Review PR using environment variables."""
    try:
        config = ReviewConfig.from_env()
        gh_poster = GitHubReviewPoster.from_env()

        reviewer = CodeReviewer(config)
        file_diffs = gh_poster.get_pr_files()

        print(f"Found {len(file_diffs)} files to review")

        pr_title = gh_poster.pr.title
        pr_description = gh_poster.pr.body or ""

        print("Running AI code review...")
        review_result = await reviewer.review_changes(
            file_diffs,
            pr_title=pr_title,
            pr_description=pr_description,
        )

        print("Posting review to GitHub...")
        gh_poster.post_review(review_result)

        print("\n" + "=" * 80)
        print("Review Summary:")
        print("=" * 80)
        print(review_result.summary)
        print(f"\nTotal comments: {len(review_result.comments)}")
        print(f"Approved: {review_result.approved}")

        sys.exit(0 if review_result.approved else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()
