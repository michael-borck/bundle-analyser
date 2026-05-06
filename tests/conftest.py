import pytest
from pathlib import Path
import zipfile
import tempfile


@pytest.fixture
def sample_folder(tmp_path):
    """A folder with a mix of file types."""
    (tmp_path / "report.txt").write_text("hello world")
    (tmp_path / "data.csv").write_text("a,b\n1,2")
    (tmp_path / "unknown.xyz").write_text("binary")
    sub = tmp_path / "subdir"
    sub.mkdir()
    (sub / "notes.txt").write_text("notes")
    return tmp_path


@pytest.fixture
def sample_zip(tmp_path, sample_folder):
    """A zip archive of the sample folder."""
    zip_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in sample_folder.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(sample_folder))
    return zip_path
