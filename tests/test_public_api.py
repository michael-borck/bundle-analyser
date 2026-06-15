"""Canonical public surface (see lens-analysers/CONVENTIONS.md).

bundle-analyser is an orchestrator: it exposes a ``BundleAnalyser`` facade, the
``BundleAnalysis`` result (alias of ``BundleAnalysisResult``), a module-level
``analyse()``, ``MANIFEST`` and ``__version__``.
"""

from __future__ import annotations

import bundle_analyser


def test_canonical_surface_importable():
    from bundle_analyser import (  # noqa: F401
        MANIFEST,
        BundleAnalyser,
        BundleAnalysis,
        BundleAnalysisResult,
        analyse,
    )

    assert callable(analyse)
    assert callable(BundleAnalyser)
    assert BundleAnalysis is BundleAnalysisResult
    assert MANIFEST["name"] == "bundle-analyser"
    assert isinstance(bundle_analyser.__version__, str)


def test_surface_in_dunder_all():
    for name in (
        "BundleAnalyser",
        "BundleAnalysis",
        "analyse",
        "MANIFEST",
        "__version__",
    ):
        assert name in bundle_analyser.__all__
