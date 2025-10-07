"""Tests for models.py."""

import pytest
import importlib
from pydantic import ValidationError

models = importlib.import_module('any-llm-code-review.models')
ReviewComment = models.ReviewComment
CodeReviewResponse = models.CodeReviewResponse


class TestReviewComment:
    """Tests for ReviewComment model."""

    def test_create_review_comment_with_all_fields(self):
        """Test creating a ReviewComment with all fields."""
        comment = ReviewComment(
            path="src/test.py",
            line=42,
            severity="error",
            category="security",
            message="SQL injection vulnerability detected",
            suggestion="Use parameterized queries"
        )

        assert comment.path == "src/test.py"
        assert comment.line == 42
        assert comment.severity == "error"
        assert comment.category == "security"
        assert comment.message == "SQL injection vulnerability detected"
        assert comment.suggestion == "Use parameterized queries"

    def test_create_review_comment_without_suggestion(self):
        """Test creating a ReviewComment without optional suggestion."""
        comment = ReviewComment(
            path="src/test.py",
            line=42,
            severity="info",
            category="style",
            message="Consider adding type hints"
        )

        assert comment.suggestion is None

    def test_severity_must_be_valid(self):
        """Test that severity must be one of the allowed values."""
        with pytest.raises(ValidationError):
            ReviewComment(
                path="src/test.py",
                line=42,
                severity="critical",
                category="bug",
                message="Test message"
            )

    def test_required_fields(self):
        """Test that all required fields must be provided."""
        with pytest.raises(ValidationError):
            ReviewComment(
                path="src/test.py",
                line=42,
            )

    def test_line_coerces_to_integer(self):
        """Test that line number coerces string to integer."""
        comment = ReviewComment(
            path="src/test.py",
            line="42",
            severity="error",
            category="bug",
            message="Test message"
        )
        assert comment.line == 42
        assert isinstance(comment.line, int)


class TestCodeReviewResponse:
    """Tests for CodeReviewResponse model."""

    def test_create_code_review_response_with_comments(self, sample_code_review_response):
        """Test creating a CodeReviewResponse with comments."""
        assert sample_code_review_response.summary == "Overall the code looks good with minor improvements needed."
        assert len(sample_code_review_response.comments) == 2
        assert sample_code_review_response.approved is False

    def test_create_code_review_response_empty_comments(self):
        """Test creating a CodeReviewResponse with no comments."""
        response = CodeReviewResponse(
            summary="Code looks great!",
            approved=True
        )

        assert response.summary == "Code looks great!"
        assert response.comments == []
        assert response.approved is True

    def test_approved_must_be_boolean(self):
        """Test that approved must be a boolean (or coercible)."""
        response = CodeReviewResponse(
            summary="Test summary",
            approved=True
        )
        assert response.approved is True
        assert isinstance(response.approved, bool)

    def test_comments_must_be_list_of_review_comments(self):
        """Test that comments must be a list of ReviewComment objects."""
        with pytest.raises(ValidationError):
            CodeReviewResponse(
                summary="Test summary",
                comments=["invalid comment"],
                approved=True
            )

    def test_required_fields_code_review_response(self):
        """Test that required fields must be provided."""
        with pytest.raises(ValidationError):
            CodeReviewResponse(
                summary="Test summary"
            )

    def test_model_serialization(self, sample_review_comment):
        """Test that models can be serialized to dict."""
        comment_dict = sample_review_comment.model_dump()

        assert comment_dict["path"] == "src/example.py"
        assert comment_dict["line"] == 10
        assert comment_dict["severity"] == "warning"

    def test_model_json_serialization(self, sample_code_review_response):
        """Test that models can be serialized to JSON."""
        json_str = sample_code_review_response.model_dump_json()

        assert isinstance(json_str, str)
        assert "Overall the code looks good" in json_str
        assert "src/example.py" in json_str
