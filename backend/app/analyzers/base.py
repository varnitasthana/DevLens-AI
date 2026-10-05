from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class NormalizedFinding:
    file: str
    line: int
    column: int
    rule: str
    category: str
    severity: str
    message: str
    source: str = "static"
    evidence: str | None = None
    remediation: str | None = None


class Analyzer(Protocol):
    def analyze(self, path: Path, relative_path: str) -> list[NormalizedFinding]:
        ...
