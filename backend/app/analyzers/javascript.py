import re
from pathlib import Path

from app.analyzers.base import NormalizedFinding


class JavaScriptAnalyzer:
    patterns = (
        (re.compile(r"\beval\s*\("), "javascript.eval", "security", "high", "Use of eval executes dynamic code.", "Avoid eval and parse input explicitly."),
        (re.compile(r"\bconsole\.log\s*\("), "javascript.console-log", "maintainability", "low", "Debug logging remains in source code.", "Use the application logging abstraction or remove debug output."),
        (re.compile(r"\binnerHTML\s*="), "javascript.inner-html", "security", "medium", "Direct innerHTML assignment can enable XSS.", "Prefer textContent or a safely escaped rendering path."),
    )

    def analyze(self, path: Path, relative_path: str) -> list[NormalizedFinding]:
        findings: list[NormalizedFinding] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern, rule, category, severity, message, remediation in self.patterns:
                match = pattern.search(line)
                if match:
                    findings.append(NormalizedFinding(relative_path, line_number, match.start() + 1, rule, category, severity, message, evidence=line.strip()[:500], remediation=remediation))
        return findings
