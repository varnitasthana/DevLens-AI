from pathlib import Path

from app.analyzers.javascript import JavaScriptAnalyzer
from app.analyzers.python import PythonAnalyzer


def test_python_analyzer_finds_eval_and_bare_except(tmp_path: Path) -> None:
    path = tmp_path / "bad.py"
    path.write_text("value = eval(user_input)\ntry:\n    pass\nexcept:\n    pass\n")

    findings = PythonAnalyzer().analyze(path, "bad.py")

    assert {finding.rule for finding in findings} == {"python.eval", "python.bare-except"}
    assert all(finding.source == "static" for finding in findings)


def test_javascript_analyzer_finds_dangerous_patterns(tmp_path: Path) -> None:
    path = tmp_path / "bad.js"
    path.write_text("element.innerHTML = value;\nconsole.log(value);\n")

    findings = JavaScriptAnalyzer().analyze(path, "bad.js")

    assert {finding.rule for finding in findings} == {
        "javascript.inner-html",
        "javascript.console-log",
    }
