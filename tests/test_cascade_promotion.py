"""Cascade promotion — implicit second passes become first-class FileResults.

auto-analyser (>=0.8) returns `cascades` (list) plus the legacy singular
`cascade`; bundle-analyser promotes each block to a FileResult with
`via="cascade:<triggered_by>"` so consumers resolve signal paths by member
name, and the human marker can see the signal set was auto-detected.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from bundle_analyser.core import analyse_bundle


def _proc(payload: dict) -> MagicMock:
    m = MagicMock()
    m.returncode = 0
    m.stdout = json.dumps(payload)
    m.stderr = ""
    return m


PAYLOAD = {
    "routed_to": "document-analyser",
    "text": "essay text",
    "cascades": [
        {
            "triggered_by": "document-analyser.heuristic",
            "routed_to": "conversation-analyser",
            "result": {"analytics": {"turn_count": 4}},
        },
        {
            "triggered_by": "document-analyser.heuristic",
            "routed_to": "reflection-analyser",
            "error": "reflection-analyser exited with code 1: boom",
        },
    ],
}


def test_cascade_rows_promoted(tmp_path):
    (tmp_path / "essay.docx").write_bytes(b"PK")
    with patch("bundle_analyser.core.subprocess.run", return_value=_proc(PAYLOAD)):
        result = analyse_bundle(str(tmp_path))

    rows = {r.analyser: r for r in result.results}
    assert set(rows) == {
        "document-analyser",
        "conversation-analyser",
        "reflection-analyser",
    }

    primary = rows["document-analyser"]
    assert primary.via is None and primary.error is None

    conv = rows["conversation-analyser"]
    assert conv.via == "cascade:document-analyser.heuristic"
    assert conv.result == {"analytics": {"turn_count": 4}}
    assert conv.error is None

    refl = rows["reflection-analyser"]
    assert refl.via == "cascade:document-analyser.heuristic"
    assert refl.error and "boom" in refl.error


def test_cascade_rows_do_not_inflate_rollups(tmp_path):
    (tmp_path / "essay.docx").write_bytes(b"PK")
    with patch("bundle_analyser.core.subprocess.run", return_value=_proc(PAYLOAD)):
        result = analyse_bundle(str(tmp_path))

    # analysed_files counts FILES, not signal sets: 1 primary, not 3.
    assert result.analysed_files == 1
    assert result.file_type_distribution == {"docx": 1}
    # A failed cascade is not a bundle-level file error either.
    assert result.errors == []


def test_legacy_singular_cascade_still_promoted(tmp_path):
    legacy = {
        "routed_to": "image-analyser",
        "cascade": {
            "triggered_by": "image-analyser.diagram.is_diagram",
            "routed_to": "diagram-analyser",
            "result": {"diagram_type": "flowchart"},
        },
    }
    (tmp_path / "pic.png").write_bytes(b"\x89PNG")
    with patch("bundle_analyser.core.subprocess.run", return_value=_proc(legacy)):
        result = analyse_bundle(str(tmp_path))

    rows = {r.analyser: r for r in result.results}
    assert set(rows) == {"image-analyser", "diagram-analyser"}
    assert rows["diagram-analyser"].via == "cascade:image-analyser.diagram.is_diagram"
    assert rows["diagram-analyser"].result == {"diagram_type": "flowchart"}
