import re

from app.schemas.dashboard import PullRequestReviewResponse


class PullRequestReviewService:
    def review_diff(self, diff: str) -> PullRequestReviewResponse:
        if not diff.strip():
            return PullRequestReviewResponse(summary="No changed lines were supplied.", issues=[], testing_recommendations=[])
        issues: list[dict[str, str]] = []
        changed_files = re.findall(r"^\+\+\+ b/(.+)$", diff, re.MULTILINE)
        added_lines = re.findall(r"^\+(?!\+\+\+)(.*)$", diff, re.MULTILINE)
        for file_name in changed_files:
            if file_name.endswith(".py") and any("eval(" in line or "exec(" in line for line in added_lines):
                issues.append({
                    "file": file_name,
                    "severity": "high",
                    "issue": "Dynamic execution was added in the pull request.",
                    "suggested_fix": "Replace dynamic execution with explicit parsing or dispatch.",
                })
            if file_name.endswith((".js", ".jsx", ".ts", ".tsx")) and any("innerHTML" in line for line in added_lines):
                issues.append({
                    "file": file_name,
                    "severity": "high",
                    "issue": "Direct HTML injection was added in the pull request.",
                    "suggested_fix": "Use safe text rendering or sanitize untrusted HTML.",
                })
        return PullRequestReviewResponse(
            summary=f"Reviewed {len(changed_files)} changed file(s) and {len(added_lines)} added line(s).",
            issues=issues,
            testing_recommendations=["Add or update tests for each changed behavior."],
        )
