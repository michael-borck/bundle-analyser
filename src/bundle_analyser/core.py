from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .models import BundleAnalysisResult, FileResult


def _walk_folder(folder: Path) -> list[Path]:
    """Recursively walk a folder, skipping hidden files/dirs and __pycache__."""
    files: list[Path] = []
    for item in sorted(folder.rglob("*")):
        # Skip hidden files/dirs (any component starting with '.')
        parts = item.relative_to(folder).parts
        if any(p.startswith(".") for p in parts):
            continue
        # Skip __pycache__ directories
        if "__pycache__" in parts:
            continue
        if item.is_file():
            files.append(item)
    return files


def _analyse_file(file_path: Path, rel_path: str) -> FileResult:
    """Call auto-analyser on a single file and return a FileResult."""
    try:
        proc = subprocess.run(
            ["auto-analyser", "analyse", str(file_path), "--json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        return FileResult(
            file=rel_path,
            analyser=None,
            result=None,
            error="auto-analyser is not installed or not on PATH",
        )
    except subprocess.TimeoutExpired:
        return FileResult(
            file=rel_path,
            analyser=None,
            result=None,
            error=f"Timed out after 120 seconds analysing {rel_path}",
        )
    except Exception as exc:
        return FileResult(
            file=rel_path,
            analyser=None,
            result=None,
            error=f"Unexpected error: {exc}",
        )

    if proc.returncode != 0:
        stderr = proc.stderr.strip() if proc.stderr else "unknown error"
        return FileResult(
            file=rel_path,
            analyser=None,
            result=None,
            error=f"auto-analyser exited with code {proc.returncode}: {stderr}",
        )

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return FileResult(
            file=rel_path,
            analyser=None,
            result=None,
            error=f"Could not parse auto-analyser output: {exc}",
        )

    analyser = data.get("routed_to")
    return FileResult(
        file=rel_path,
        analyser=analyser,
        result=data,
        error=None,
    )


def _extension_distribution(results: list[FileResult]) -> dict[str, int]:
    """Count files by extension (lowercased, without the leading dot)."""
    dist: dict[str, int] = {}
    for r in results:
        ext = Path(r.file).suffix.lstrip(".").lower()
        if ext:
            dist[ext] = dist.get(ext, 0) + 1
        else:
            dist["(no extension)"] = dist.get("(no extension)", 0) + 1
    return dist


def analyse_bundle(source: str | Path) -> BundleAnalysisResult:
    """Analyse a folder or zip archive, dispatching each file to auto-analyser."""
    source = str(source)

    # Reject URLs
    if source.startswith("http://") or source.startswith("https://") or source.startswith("git://"):
        return BundleAnalysisResult(
            source=source,
            source_type="unknown",
            total_files=0,
            analysed_files=0,
            unrecognised_files=[],
            errors=[],
            file_type_distribution={},
            results=[],
            error="bundle-analyser accepts local paths only. For git repositories, use git-analyser.",
        )

    path = Path(source)

    # Check existence
    if not path.exists():
        return BundleAnalysisResult(
            source=source,
            source_type="unknown",
            total_files=0,
            analysed_files=0,
            unrecognised_files=[],
            errors=[],
            file_type_distribution={},
            results=[],
            error=f"Path not found: {source}",
        )

    # Determine type
    if path.is_dir():
        source_type = "folder"
        return _analyse_folder(path, source, source_type)
    elif path.is_file() and path.suffix.lower() == ".zip":
        source_type = "zip"
        return _analyse_zip(path, source, source_type)
    else:
        return BundleAnalysisResult(
            source=source,
            source_type="unknown",
            total_files=0,
            analysed_files=0,
            unrecognised_files=[],
            errors=[],
            file_type_distribution={},
            results=[],
            error="Expected a folder or .zip file.",
        )


def _analyse_folder(
    folder: Path, source: str, source_type: str
) -> BundleAnalysisResult:
    """Walk a folder and analyse each file."""
    all_files = _walk_folder(folder)
    results: list[FileResult] = []
    unrecognised: list[str] = []
    errors: list[str] = []

    for file_path in all_files:
        rel_path = str(file_path.relative_to(folder))
        fr = _analyse_file(file_path, rel_path)
        results.append(fr)
        if fr.error:
            errors.append(f"{rel_path}: {fr.error}")
        elif fr.analyser is None:
            unrecognised.append(rel_path)

    analysed = sum(1 for r in results if r.error is None and r.analyser is not None)

    return BundleAnalysisResult(
        source=source,
        source_type=source_type,
        total_files=len(all_files),
        analysed_files=analysed,
        unrecognised_files=unrecognised,
        errors=errors,
        file_type_distribution=_extension_distribution(results),
        results=results,
        error=None,
    )


def _analyse_zip(zip_path: Path, source: str, source_type: str) -> BundleAnalysisResult:
    """Extract a zip archive and analyse its contents (one level only)."""
    import zipfile

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Extract all members except nested zips (those go to unrecognised)
            members = zf.namelist()
            for member in members:
                member_path = Path(member)
                # Skip directories
                if member.endswith("/"):
                    continue
                # Do NOT extract nested zip files — they'll be noted as unrecognised
                if member_path.suffix.lower() == ".zip":
                    continue
                zf.extract(member, tmp_dir)

        # Walk the extracted tree
        all_files = _walk_folder(tmp_dir)

        # Collect nested zip names for unrecognised list
        nested_zips = [
            m for m in members
            if not m.endswith("/") and Path(m).suffix.lower() == ".zip"
        ]

        results: list[FileResult] = []
        unrecognised: list[str] = list(nested_zips)
        errors: list[str] = []

        for file_path in all_files:
            rel_path = str(file_path.relative_to(tmp_dir))
            fr = _analyse_file(file_path, rel_path)
            results.append(fr)
            if fr.error:
                errors.append(f"{rel_path}: {fr.error}")
            elif fr.analyser is None:
                unrecognised.append(rel_path)

        # total_files includes nested zips that were not extracted
        total_files = len(all_files) + len(nested_zips)
        analysed = sum(1 for r in results if r.error is None and r.analyser is not None)

        return BundleAnalysisResult(
            source=source,
            source_type=source_type,
            total_files=total_files,
            analysed_files=analysed,
            unrecognised_files=unrecognised,
            errors=errors,
            file_type_distribution=_extension_distribution(results),
            results=results,
            error=None,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
