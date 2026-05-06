from __future__ import annotations

import json
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


def test_rejects_http_url():
    result = analyse_bundle("http://example.com/files.zip")
    assert result.error is not None
    assert "git-analyser" in result.error


def test_rejects_non_zip_file(tmp_path):
    f = tmp_path / "document.pdf"
    f.write_bytes(b"%PDF fake")
    result = analyse_bundle(str(f))
    assert result.error is not None


# ---------------------------------------------------------------------------
# Folder analysis tests (subprocess mocked)
# ---------------------------------------------------------------------------

def test_folder_structure(sample_folder):
    with patch("bundle_analyser.core.subprocess.run", return_value=make_mock_proc()):
        result = analyse_bundle(str(sample_folder))
    assert result.error is None
    assert result.source_type == "folder"
    assert result.total_files >= 4


def test_zip_structure(sample_zip):
    with patch("bundle_analyser.core.subprocess.run", return_value=make_mock_proc()):
        result = analyse_bundle(str(sample_zip))
    assert result.error is None
    assert result.source_type == "zip"
    assert result.total_files >= 4


def test_file_type_distribution(sample_folder):
    with patch("bundle_analyser.core.subprocess.run", return_value=make_mock_proc()):
        result = analyse_bundle(str(sample_folder))
    assert result.error is None
    assert "txt" in result.file_type_distribution


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
