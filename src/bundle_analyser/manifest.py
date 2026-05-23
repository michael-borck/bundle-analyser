"""Capability manifest for the lens family (consumed by auto-analyser).

bundle-analyser is an orchestrator over collections (folders/zips), invoked
explicitly rather than routed to by file extension.
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def _version() -> str:
    try:
        return version("bundle-analyser")
    except PackageNotFoundError:
        return "0.0.0"


MANIFEST: dict = {
    "name": "bundle-analyser",
    "version": _version(),
    "role": "orchestrator",
    "accepts": ["bundle", "folder", "zip"],
    "extensions": [],
    "auto_routable": False,
    "produces": "BundleAnalysisResult",
}
