"""Tests for the optional Streamlit UI in ``app.py``.

Streamlit is an optional dependency, so ``app.py`` is exercised against a
minimal stub module inside a subprocess. That keeps ``sys.modules`` clean for
the rest of the suite while still executing every UI code path (so a typo in
an attribute name or dict key fails the build).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
VERIFY = ROOT / "verify_app.py"
APP = ROOT / "app.py"


def test_app_module_exists() -> None:
    assert APP.is_file(), "optional Streamlit UI (app.py) is missing"


def test_verify_script_exists() -> None:
    assert VERIFY.is_file(), "verify_app.py stub harness is missing"


def test_app_is_valid_python_syntax() -> None:
    compile(APP.read_text(encoding="utf-8"), str(APP), "exec")


@pytest.mark.parametrize(
    "marker",
    [
        "render_prediction",
        "comparison_matrix",
        "team_panel",
        "card_row",
        "deck_browser",
        "sidebar",
        "set_page_config",
    ],
)
def test_app_defines_expected_structure(marker: str) -> None:
    assert marker in APP.read_text(encoding="utf-8")


def test_app_renders_every_path_without_streamlit_installed() -> None:
    """The stub harness must pass: no AttributeError / TypeError anywhere."""
    result = subprocess.run(
        [sys.executable, str(VERIFY)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"app.py plumbing failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "app.py plumbing verified" in result.stdout


def test_app_does_not_use_private_engine_attributes() -> None:
    """engine._data does not exist; the UI must use the public API."""
    source = APP.read_text(encoding="utf-8")
    assert "engine._data" not in source
    assert "_data[" not in source


def test_app_never_reads_a_raw_json_file() -> None:
    """The engine owns loading; the UI should not bypass it."""
    source = APP.read_text(encoding="utf-8")
    assert "json.load" not in source
    assert "open(" not in source