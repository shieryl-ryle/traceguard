"""TC-001 (data part) and TC-012: exactly C-1..C-3 from a seeded, reproducible generator."""

import subprocess
import sys
from pathlib import Path

from traceguard.graph.loader import case_dicts, load_dataset

ROOT = Path(__file__).resolve().parents[1]


def test_exactly_three_labelled_cases() -> None:
    cases = load_dataset().cases
    assert [c["case_id"] for c in cases] == ["C-1", "C-2", "C-3"]
    for case in cases:
        assert case["scenario_label"] and case["title"] and case["seed_ids"]


def test_case_dicts_have_ui_shape() -> None:
    for view in case_dicts():
        assert set(view) == {"case", "accounts", "device_links", "transactions"}
        assert all(t["currency"] == "PHP" for t in view["transactions"])


def test_dataset_is_marked_synthetic_and_reproducible() -> None:
    assert "SYNTHETIC" in load_dataset().raw["_note"]
    result = subprocess.run([sys.executable, str(ROOT / "data" / "generate.py"), "--check"],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
