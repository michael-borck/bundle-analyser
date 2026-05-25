"""Capability manifest for the lens family (consumed by auto-analyser).

bundle-analyser is an orchestrator over collections (folders/zips), invoked
explicitly rather than routed to by file extension.
"""
from __future__ import annotations

from lens_contract import make_manifest

MANIFEST = make_manifest(
    name="bundle-analyser",
    role="orchestrator",
    accepts=["bundle", "folder", "zip"],
    extensions=[],
    auto_routable=False,
    produces="BundleAnalysisResult",
)
