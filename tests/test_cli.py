from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _python() -> str:
    """Return a Python interpreter that has bundle_analyser installed.

    When running under uv the active interpreter may differ from the project
    venv.  Prefer the venv at <project-root>/.venv if it exists so that
    bundle_analyser is importable.
    """
    # Walk up from this file to find the project root (contains pyproject.toml)
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent, here.parent.parent.parent]:
        venv_python = parent / ".venv" / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)
    # Fallback: use the running interpreter
    return sys.executable


def test_help_exits_zero():
    result = subprocess.run(
        [_python(), "-m", "bundle_analyser.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "bundle-analyser" in result.stdout.lower() or "usage" in result.stdout.lower()


def test_serve_help_exits_zero():
    result = subprocess.run(
        [_python(), "-m", "bundle_analyser.cli", "serve", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
