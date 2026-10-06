import pytest

from app.schemas.dashboard import GitHubImportRequest
from app.services.github import GitHubImportService
from app.services.pull_request_review import PullRequestReviewService


class FakeGitHubClient:
    def repository(self, owner: str, name: str) -> dict[str, object]:
        assert (owner, name) == ("example", "sample")
        return {
            "full_name": "example/sample",
            "html_url": "https://github.com/example/sample",
            "default_branch": "main",
            "description": "Sample repository",
        }


def test_pull_request_review_analyzes_added_lines_only() -> None:
    result = PullRequestReviewService().review_diff(
        "diff --git a/app.py b/app.py\n"
        "+++ b/app.py\n"
        "@@ -1 +1 @@\n"
        "-value = eval(old_value)\n"
        "+value = eval(user_input)\n"
    )
    assert result.issues[0]["severity"] == "high"
    assert result.testing_recommendations


def test_pull_request_review_empty_diff_is_safe() -> None:
    result = PullRequestReviewService().review_diff("")
    assert result.issues == []


def test_github_url_validation_requires_github_repository() -> None:
    with pytest.raises(Exception):
        GitHubImportService(None, FakeGitHubClient()).import_repository(
            GitHubImportRequest(url="https://gitlab.com/example/sample")
        )
