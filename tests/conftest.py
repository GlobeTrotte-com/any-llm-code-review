"""Pytest fixtures for tests."""

import pytest
import importlib

models = importlib.import_module('any-llm-code-review.models')
config = importlib.import_module('any-llm-code-review.config')

ReviewComment = models.ReviewComment
CodeReviewResponse = models.CodeReviewResponse
ReviewConfig = config.ReviewConfig


@pytest.fixture
def sample_review_comment():
    """Sample ReviewComment for testing."""
    return ReviewComment(
        path="src/example.py",
        line=10,
        severity="warning",
        category="performance",
        message="This loop could be optimized",
        suggestion="Use list comprehension instead"
    )


@pytest.fixture
def sample_code_review_response():
    """Sample CodeReviewResponse for testing."""
    return CodeReviewResponse(
        summary="Overall the code looks good with minor improvements needed.",
        comments=[
            ReviewComment(
                path="src/example.py",
                line=10,
                severity="warning",
                category="performance",
                message="This loop could be optimized",
                suggestion="Use list comprehension instead"
            ),
            ReviewComment(
                path="src/example.py",
                line=25,
                severity="error",
                category="bug",
                message="Potential null pointer exception",
            )
        ],
        approved=False
    )


@pytest.fixture
def sample_review_config():
    """Sample ReviewConfig for testing."""
    return ReviewConfig(
        model_provider="openai",
        model_name="gpt-4",
        api_key="test-api-key",
        github_token="test-github-token",
        max_tokens=4000,
        temperature=0.3,
    )


@pytest.fixture
def sample_diff():
    """Sample git diff for testing."""
    return """@@ -1,5 +1,6 @@
 def calculate_total(items):
     total = 0
     for item in items:
         total += item.price
+    print(f"Total: {total}")
     return total
"""


@pytest.fixture
def sample_file_changes():
    """Sample file changes dictionary for testing."""
    return {
        "src/main.py": """@@ -10,3 +10,4 @@
 def process_data(data):
     result = []
     for item in data:
         result.append(item * 2)
+    return result
""",
        "src/utils.py": """@@ -5,2 +5,3 @@
 def helper_function(x):
+    # Added comment
     return x + 1
"""
    }
