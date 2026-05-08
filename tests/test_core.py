from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bundle_analyser.core import analyse_bundle

FAKE_RESULT = json.dumps({"routed_to": "document-analyser", "word_count": 100})


def make_mock_proc(returncode=0, stdout=FAKE_RESULT, stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


# ---------------------------------------------------------------------------
# Input validation tests (no subprocess needed)
# ---------------------------------------------------------------------------

def test_nonexistent_path():
    result = analyse_bundle("/tmp/__does_not_exist_bundle_analyser__")
    assert result.error is not None
    assert "not found" in result.error.lower() or "Path not found" in result.error


def test_rejects_url():
    result = analyse_bundle("https://github.com/example/repo")
    assert result.error is not None
    assert "git-analyser" in result.error


def test_rejects_non_zip_file(tmp_path):
    f = tmp_path / "document.pdf"
    f.write_bytes(b"%PDF fake")
    result = analyse_bundle(str(f))
    assert result.error is not None
    # The error message should mention zip or folder expectation
    assert "zip" in result.error.lower() or "folder" in result.error.lower()


# ---------------------------------------------------------------------------
# Folder analysis tests (subprocess mocked)
# ---------------------------------------------------------------------------

def test_folder_structure(sample_folder):
    with patch("bundle_analyser.core.subprocess.run", return_value=make_mock_proc()) as mock_run:
        result = analyse_bundle(str(sample_folder))
    assert result.error is None
    assert result.source_type == "folder"
    assert result.total_files >= 4

    # Verify the right command + flags are dispatched (not just that the mock returned)
    called_args = mock_run.call_args_list
    assert len(called_args) >= 1
    for call in called_args:
        cmd = call.args[0]
        assert cmd[0] == "auto-analyser"
        assert cmd[1] == "analyse"
        assert cmd[-1] == "--json"


def test_zip_structure(sample_zip):
    with patch("bundle_analyser.core.subprocess.run", return_value=make_mock_proc()) as mock_run:
        result = analyse_bundle(str(sample_zip))
    assert result.error is None
    assert result.source_type == "zip"
    assert result.total_files >= 4

    # Verify the right command + flags are dispatched
    called_args = mock_run.call_args_list
    assert len(called_args) >= 1
    for call in called_args:
        cmd = call.args[0]
        assert cmd[0] == "auto-analyser"
        assert cmd[1] == "analyse"
        assert cmd[-1] == "--json"


def test_file_type_distribution(sample_folder):
    with patch("bundle_analyser.core.subprocess.run", return_value=make_mock_proc()):
        result = analyse_bundle(str(sample_folder))
    assert result.error is None
    # sample_folder fixture has: report.txt, data.csv, unknown.xyz, subdir/notes.txt
    assert result.file_type_distribution.get("txt") == 2
    assert result.file_type_distribution.get("csv") == 1
    assert result.file_type_distribution.get("xyz") == 1


def test_unrecognised_files(sample_folder):
    """When auto-analyser returns routed_to=None, the file goes to unrecognised_files."""
    fake_unrecognised = json.dumps({"routed_to": None})

    def side_effect(cmd, **kwargs):
        # Return unrecognised for .xyz files, normal result for others
        if "unknown.xyz" in " ".join(str(c) for c in cmd):
            return make_mock_proc(stdout=fake_unrecognised)
        return make_mock_proc()

    with patch("bundle_analyser.core.subprocess.run", side_effect=side_effect):
        result = analyse_bundle(str(sample_folder))

    assert result.error is None
    # unknown.xyz should appear in unrecognised_files
    unrecognised_names = [Path(p).name for p in result.unrecognised_files]
    assert "unknown.xyz" in unrecognised_names


def test_errors_recorded_not_abort(sample_folder):
    """If one file errors, the rest should still be analysed."""
    def side_effect(cmd, **kwargs):
        if "data.csv" in " ".join(str(c) for c in cmd):
            return make_mock_proc(returncode=1, stdout="", stderr="unsupported")
        return make_mock_proc()

    with patch("bundle_analyser.core.subprocess.run", side_effect=side_effect):
        result = analyse_bundle(str(sample_folder))

    assert result.error is None
    assert any("data.csv" in e for e in result.errors)
    # Other files were still analysed
    assert result.analysed_files >= 1


def test_auto_analyser_not_installed(sample_folder):
    """FileNotFoundError from subprocess → per-file error, no abort."""
    with patch(
        "bundle_analyser.core.subprocess.run",
        side_effect=FileNotFoundError("auto-analyser not found"),
    ):
        result = analyse_bundle(str(sample_folder))
    assert result.error is None
    assert len(result.errors) == result.total_files


def test_auto_analyser_returns_invalid_json(sample_folder):
    """If auto-analyser prints non-JSON to stdout, the error is recorded
    per-file (not a crash, not silently treated as success)."""
    bad_proc = make_mock_proc(returncode=0, stdout="not valid json {oops")

    with patch("bundle_analyser.core.subprocess.run", return_value=bad_proc):
        result = analyse_bundle(str(sample_folder))

    assert result.error is None
    assert len(result.errors) > 0
    # Error message should mention JSON parsing
    assert any("parse" in err.lower() or "json" in err.lower() for err in result.errors)


def test_per_file_timeout_records_error(sample_folder):
    """A subprocess timeout on one file is recorded as an error,
    other files still process (and the bundle as a whole does not abort)."""
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="auto-analyser", timeout=120)

    with patch("bundle_analyser.core.subprocess.run", side_effect=fake_run):
        result = analyse_bundle(str(sample_folder))

    # All files should be in errors (every subprocess call timed out)
    assert result.error is None
    assert len(result.errors) == result.total_files
    # Error message should mention the timeout
    assert any("timed out" in err.lower() or "timeout" in err.lower() for err in result.errors)


def test_nested_zip_listed_as_unrecognised(tmp_path):
    """Bundle does ONE level of zip extraction. Nested zips are listed
    in unrecognised_files, not extracted recursively."""
    inner = tmp_path / "inner.zip"
    with zipfile.ZipFile(inner, "w") as zf:
        zf.writestr("hello.txt", "hi")

    outer = tmp_path / "outer.zip"
    with zipfile.ZipFile(outer, "w") as zf:
        zf.write(inner, arcname="nested.zip")
        zf.writestr("plain.txt", "outer file")

    # Mock subprocess so plain.txt analysis doesn't fail
    with patch("bundle_analyser.core.subprocess.run", return_value=make_mock_proc()):
        result = analyse_bundle(str(outer))

    assert result.error is None
    assert "nested.zip" in result.unrecognised_files


def test_walk_skips_hidden_and_pycache(tmp_path):
    """Hidden files (.git, .DS_Store) and __pycache__ are NOT analysed."""
    (tmp_path / "visible.txt").write_text("visible")
    (tmp_path / ".hidden.txt").write_text("hidden")
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "module.cpython-313.pyc").write_bytes(b"compiled bytes")

    with patch("bundle_analyser.core.subprocess.run", return_value=make_mock_proc()):
        result = analyse_bundle(str(tmp_path))

    # Should only see visible.txt — neither .hidden.txt nor the .pyc
    analysed_paths = [r.file for r in result.results]
    assert any("visible.txt" in p for p in analysed_paths)
    assert not any("hidden" in p.lower() for p in analysed_paths)
    assert not any("__pycache__" in p for p in analysed_paths)
