from __future__ import annotations

import json
from importlib.metadata import version
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from bundle_analyser.api import app

client = TestClient(app)

FAKE_RESULT = json.dumps({"routed_to": "document-analyser", "word_count": 100})


def make_mock_proc(returncode=0, stdout=FAKE_RESULT, stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == version("bundle-analyser")


# ---------------------------------------------------------------------------
# POST /analyse
# ---------------------------------------------------------------------------

def test_analyse_nonexistent_path():
    response = client.post("/analyse", json={"path": "/tmp/__does_not_exist_bundle__"})
    assert response.status_code == 400


def test_analyse_valid_folder(sample_folder):
    with patch("bundle_analyser.core.subprocess.run", return_value=make_mock_proc()) as mock_run:
        response = client.post("/analyse", json={"path": str(sample_folder)})
    assert response.status_code == 200
    data = response.json()
    assert data["source_type"] == "folder"
    assert data["total_files"] >= 4

    # Verify the right command + flags are dispatched
    called_args = mock_run.call_args_list
    assert len(called_args) >= 1
    for call in called_args:
        cmd = call.args[0]
        assert cmd[0] == "auto-analyser"
        assert cmd[1] == "analyse"
        assert cmd[-1] == "--json"


def test_analyse_url_rejected():
    response = client.post("/analyse", json={"path": "https://github.com/example/repo"})
    assert response.status_code == 400
    assert "git-analyser" in response.json()["detail"]


# ---------------------------------------------------------------------------
# POST /analyse/upload
# ---------------------------------------------------------------------------

def test_upload_non_zip():
    response = client.post(
        "/analyse/upload",
        files={"file": ("document.pdf", b"%PDF fake content", "application/pdf")},
    )
    assert response.status_code == 400
    assert "zip" in response.json()["detail"].lower()


def test_upload_valid_zip(sample_zip):
    with patch("bundle_analyser.core.subprocess.run", return_value=make_mock_proc()) as mock_run:
        with open(sample_zip, "rb") as f:
            response = client.post(
                "/analyse/upload",
                files={"file": ("bundle.zip", f, "application/zip")},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["source_type"] == "zip"
    assert data["total_files"] >= 4

    # Verify the right command + flags are dispatched
    called_args = mock_run.call_args_list
    assert len(called_args) >= 1
    for call in called_args:
        cmd = call.args[0]
        assert cmd[0] == "auto-analyser"
        assert cmd[1] == "analyse"
        assert cmd[-1] == "--json"
