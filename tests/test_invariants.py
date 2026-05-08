"""Invariant tests — fast, mocked, run by default."""

from importlib.metadata import version
from unittest.mock import patch


def test_package_imports_cleanly() -> None:
    """Smoke alarm — package must import without errors."""
    import bundle_analyser  # noqa: F401
    from bundle_analyser.cli import main  # noqa: F401
    from bundle_analyser.api import app  # noqa: F401


def test_health_version_matches_installed_package() -> None:
    """/health must report the actual installed package version."""
    from fastapi.testclient import TestClient

    from bundle_analyser.api import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == version("bundle-analyser")


def test_unknown_extension_goes_to_unrecognised(tmp_path) -> None:
    """Bundle's contract: don't crash on files auto-analyser doesn't know."""
    from bundle_analyser.core import analyse_bundle

    f = tmp_path / "mystery.xyz"
    f.write_text("data")

    # Mock so auto-analyser returns "unknown format" error for .xyz
    with patch("bundle_analyser.core.subprocess.run") as mock_run:
        mock_run.return_value = type(
            "Proc",
            (),
            {
                "returncode": 1,
                "stdout": "",
                "stderr": '{"error": "Unknown format: .xyz"}',
            },
        )()
        result = analyse_bundle(tmp_path)

    # The .xyz file should land in unrecognised_files OR errors,
    # but the bundle as a whole should NOT have a top-level error
    assert result.error is None
    in_unrecognised = "mystery.xyz" in result.unrecognised_files
    in_errors = any("mystery.xyz" in err for err in result.errors)
    assert in_unrecognised or in_errors


def test_single_file_error_does_not_abort_bundle(tmp_path) -> None:
    """One file failing must NOT abort the whole bundle."""
    from bundle_analyser.core import analyse_bundle

    (tmp_path / "good.txt").write_text("hi")
    (tmp_path / "bad.csv").write_text("x")

    def selective_fake_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if any("bad.csv" in str(arg) for arg in cmd):
            return type(
                "Proc",
                (),
                {"returncode": 1, "stdout": "", "stderr": '{"error": "boom"}'},
            )()
        return type(
            "Proc",
            (),
            {
                "returncode": 0,
                "stdout": '{"routed_to": "document-analyser"}',
                "stderr": "",
            },
        )()

    with patch("bundle_analyser.core.subprocess.run", side_effect=selective_fake_run):
        result = analyse_bundle(tmp_path)

    # Bundle continues — at least the good file analysed, errors recorded
    assert result.error is None
    assert result.analysed_files >= 1
    assert any("bad.csv" in err for err in result.errors)
