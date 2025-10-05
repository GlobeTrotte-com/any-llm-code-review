"""GitHub integration for posting review comments."""

import os
from typing import Optional
from github import Github, PullRequest
from .models import CodeReviewResponse, ReviewComment


class GitHubReviewPoster:
    """Posts AI-generated code reviews to GitHub PRs."""

    def __init__(self, token: str, repository: str, pr_number: int, review_title: str = "AI Code Review"):
        """
        Initialize GitHub integration.

        Args:
            token: GitHub API token
            repository: Repository in format "owner/repo"
            pr_number: Pull request number
            review_title: Title for the review comment
        """
        self.github = Github(token)
        self.repo = self.github.get_repo(repository)
        self.pr_number = pr_number
        self.pr = self.repo.get_pull(pr_number)
        self.review_title = review_title

    def get_pr_files(self) -> dict[str, str]:
        """
        Get the diff for all files in the PR.

        Returns:
            Dict mapping file paths to their diff content
        """
        files = self.pr.get_files()
        file_diffs = {}

        for file in files:
            if file.patch:  # Some files may not have patches (e.g., binary files)
                file_diffs[file.filename] = file.patch

        return file_diffs

    def post_review(self, review: CodeReviewResponse) -> None:
        """
        Post the review to the GitHub PR.

        Args:
            review: The AI-generated code review
        """
        # GitHub Actions cannot APPROVE or REQUEST_CHANGES, only COMMENT
        # Use COMMENT event and indicate approval status in the message
        approval_status = "✅ **APPROVED**" if review.approved else "⚠️ **CHANGES REQUESTED**"

        # If there are no comments, just post a comment with the summary
        if not review.comments:
            self.pr.create_review(
                body=f"## {self.review_title}\n\n{approval_status}\n\n{review.summary}",
                event="COMMENT",
            )
            return

        # Build review comments for specific lines
        review_comments = []
        for comment in review.comments:
            severity_emoji = {
                "error": "🚨",
                "warning": "⚠️",
                "info": "💡",
            }
            emoji = severity_emoji.get(comment.severity, "")

            body = f"{emoji} **{comment.category.upper()}** ({comment.severity})\n\n{comment.message}"
            if comment.suggestion:
                body += f"\n\n**Suggested fix:**\n```\n{comment.suggestion}\n```"

            # Try to post as line comment
            try:
                review_comments.append({
                    "path": comment.path,
                    "line": comment.line,
                    "side": "RIGHT",
                    "body": body,
                })
            except Exception as e:
                # If line comment fails, we'll add it to the summary
                print(f"Warning: Could not add comment for {comment.path}:{comment.line}: {e}")

        # Post the review
        try:
            approval_status = "✅ **APPROVED**" if review.approved else "⚠️ **CHANGES REQUESTED**"

            if review_comments:
                self.pr.create_review(
                    body=f"## {self.review_title}\n\n{approval_status}\n\n{review.summary}",
                    event="COMMENT",  # Always use COMMENT since GitHub Actions can't approve
                    comments=review_comments,
                )
            else:
                # Fallback to general comment if no line comments worked
                self.pr.create_review(
                    body=f"## {self.review_title}\n\n{approval_status}\n\n{review.summary}",
                    event="COMMENT",
                )
        except Exception as e:
            print(f"Error posting review: {e}")
            # Fallback to issue comment
            comment_body = f"## {self.review_title}\n\n{review.summary}\n\n"
            for comment in review.comments:
                severity_emoji = {
                    "error": "🚨",
                    "warning": "⚠️",
                    "info": "💡",
                }
                emoji = severity_emoji.get(comment.severity, "")
                comment_body += f"\n### {emoji} {comment.path}:{comment.line}\n"
                comment_body += f"**{comment.category.upper()}** ({comment.severity})\n\n"
                comment_body += f"{comment.message}\n"
                if comment.suggestion:
                    comment_body += f"\n**Suggested fix:**\n```\n{comment.suggestion}\n```\n"

            self.pr.create_issue_comment(comment_body)

    @classmethod
    def from_env(cls) -> "GitHubReviewPoster":
        """Create from environment variables (for GitHub Actions)."""
        token = os.getenv("GITHUB_TOKEN", "")
        repository = os.getenv("GITHUB_REPOSITORY", "")
        review_title = os.getenv("REVIEW_TITLE", "AI Code Review")

        # Extract PR number from GITHUB_REF (format: refs/pull/:prNumber/merge)
        github_ref = os.getenv("GITHUB_REF", "")
        pr_number = None
        if "pull" in github_ref:
            parts = github_ref.split("/")
            if len(parts) >= 3:
                pr_number = int(parts[2])

        # Fallback to event payload
        if not pr_number:
            import json
            event_path = os.getenv("GITHUB_EVENT_PATH", "")
            if event_path and os.path.exists(event_path):
                with open(event_path, "r") as f:
                    event = json.load(f)
                    pr_number = event.get("pull_request", {}).get("number")

        if not pr_number:
            raise ValueError("Could not determine PR number from environment")

        return cls(token, repository, pr_number, review_title)
