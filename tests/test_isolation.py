"""TC-021 (BR-010): no app module reads from tests/ (expected outcomes stay test-only)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(r"\btests\b|fixtures|expected_C-|rule_config\.json")


def test_app_code_never_references_tests() -> None:
    sources = [ROOT / "app.py", *sorted((ROOT / "traceguard").rglob("*.py"))]
    offenders = [
        f"{path.relative_to(ROOT)}:{n}"
        for path in sources
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if FORBIDDEN.search(line)
    ]
    assert offenders == []
