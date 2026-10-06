import asyncio
import re

from fastapi import HTTPException, status

from app.ai.provider import OpenAICompatibleProvider
from app.ai.service import AIReviewService
from app.core.config import Settings
from app.schemas.dashboard import PullRequestReviewResponse
from app.services.github import GitHubClient


class PullRequestReviewService:
    PR_URL_PATTERN = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)")

    def __init__(
        self,
        client: GitHubClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.client = client
        self.settings = settings

    def review_diff(self, diff: str) -> PullRequestReviewResponse:
        if not diff.strip():
            return PullRequestReviewResponse(
                summary="No changed lines were supplied.",
                issues=[],
                testing_recommendations=[],
            )
        issues: list[dict[str, str]] = []
        changed_files = re.findall(r"^\+\+\+ b/(.+)$", diff, re.MULTILINE)
        added_lines = re.findall(r"^\+(?!\+\+\+)(.*)$", diff, re.MULTILINE)
        for file_name in changed_files:
            if file_name.endswith(".py") and any(
                "eval(" in line or "exec(" in line for line in added_lines
            ):
                issues.append(
                    {
                        "file": file_name,
                        "severity": "high",
                        "issue": "Dynamic execution was added in the pull request.",
                        "suggested_fix": "Replace dynamic execution with explicit parsing or dispatch.",
                        "source": "static",
                    }
                )
            if file_name.endswith((".js", ".jsx", ".ts", ".tsx")) and any(
                "innerHTML" in line for line in added_lines
            ):
                issues.append(
                    {
                        "file": file_name,
                        "severity": "high",
                        "issue": "Direct HTML injection was added in the pull request.",
                        "suggested_fix": "Use safe text rendering or sanitize untrusted HTML.",
                        "source": "static",
                    }
                )
        return PullRequestReviewResponse(
            summary=f"Reviewed {len(changed_files)} changed file(s) and {len(added_lines)} added line(s).",
            issues=issues,
            testing_recommendations=["Add or update tests for each changed behavior."],
        )

    def review_github_pr(self, url: str) -> PullRequestReviewResponse:
        if self.client is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub client is not configured",
            )
        match = self.PR_URL_PATTERN.match(url.strip())
        if not match:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid GitHub pull request URL",
            )
        owner, name, number_str = match.groups()
        number = int(number_str)
        self.client.pull_request(owner, name, number)
        diff = self.client.pull_request_diff(owner, name, number)
        result = self.review_diff(diff)
        ai_issues, ai_recommendations = self._run_ai_review(diff)
        result.issues.extend(ai_issues)
        result.testing_recommendations.extend(ai_recommendations)
        return result

    def _run_ai_review(self, diff: str) -> tuple[list[dict[str, str]], list[str]]:
        if (
            not self.settings
            or not self.settings.ai_base_url
            or not self.settings.ai_api_key
        ):
            return [], []
        changed_files = self._extract_added_lines_by_file(diff)
        if not changed_files:
            return [], []
        provider = OpenAICompatibleProvider(
            self.settings.ai_base_url,
            self.settings.ai_api_key,
            self.settings.ai_model,
            self.settings.ai_timeout_seconds,
        )
        try:
            response = asyncio.run(AIReviewService(provider).review_files(changed_files))
        except RuntimeError:
            return [], []
        ai_issues = [
            {
                "file": finding.evidence.split(":", 1)[0] if ":" in finding.evidence else "unknown",
                "severity": finding.severity,
                "issue": finding.explanation,
                "suggested_fix": finding.suggested_fix,
                "source": "ai",
            }
            for finding in response.findings
        ]
        ai_recommendations = [
            f"Consider reviewing AI finding: {finding.explanation[:80]}"
            for finding in response.findings
        ]
        return ai_issues, ai_recommendations

    @staticmethod
    def _extract_added_lines_by_file(diff: str) -> dict[str, str]:
        files: dict[str, list[str]] = {}
        current_file: str | None = None
        for line in diff.splitlines():
            match = re.match(r"^\+\+\+ b/(.+)$", line)
            if match:
                current_file = match.group(1)
                files.setdefault(current_file, [])
            elif current_file and line.startswith("+") and not line.startswith("+++"):
                content = line[1:]
                if content.strip():
                    files[current_file].append(content)
        return {path: "\n".join(lines) for path, lines in files.items() if lines}
