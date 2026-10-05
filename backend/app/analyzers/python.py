import ast
from pathlib import Path

from app.analyzers.base import NormalizedFinding


class PythonAnalyzer:
    def analyze(self, path: Path, relative_path: str) -> list[NormalizedFinding]:
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return [
                NormalizedFinding(
                    relative_path, exc.lineno or 1, exc.offset or 1, "python.syntax-error",
                    "correctness", "high", "Python syntax error", evidence=exc.msg,
                    remediation="Fix the syntax error before running the code.",
                )
            ]
        findings: list[NormalizedFinding] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "eval":
                    findings.append(self._finding(relative_path, node, "python.eval", "security", "high", "Use of eval executes dynamic input.", "Avoid eval; use explicit parsing."))
                if node.func.id == "exec":
                    findings.append(self._finding(relative_path, node, "python.exec", "security", "high", "Use of exec executes dynamic code.", "Avoid exec and use explicit, typed operations."))
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                findings.append(self._finding(relative_path, node, "python.bare-except", "maintainability", "medium", "Bare except catches every exception.", "Catch the specific exceptions the code can handle."))
            if isinstance(node, ast.FunctionDef) and len(node.body) > 50:
                findings.append(self._finding(relative_path, node, "python.long-function", "maintainability", "low", "Function body is unusually long.", "Split the function into smaller units with clear responsibilities."))
        return findings

    @staticmethod
    def _finding(path: str, node: ast.AST, rule: str, category: str, severity: str, message: str, remediation: str) -> NormalizedFinding:
        return NormalizedFinding(path, getattr(node, "lineno", 1), getattr(node, "col_offset", 0) + 1, rule, category, severity, message, remediation=remediation)
