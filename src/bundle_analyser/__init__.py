from importlib.metadata import version as _v
from pathlib import Path

from .core import analyse_bundle
from .manifest import MANIFEST
from .models import BundleAnalysisResult

__version__ = _v("bundle-analyser")
del _v

# bundle-analyser is an orchestrator (it walks a folder/zip and runs the right
# analyser per file), but it still honours the family's canonical surface.
BundleAnalysis = BundleAnalysisResult  # canonical family name alias


class BundleAnalyser:
    """Thin facade over :func:`analyse_bundle` for the family's canonical call shape."""

    def analyse(self, source: str | Path) -> BundleAnalysisResult:
        return analyse_bundle(source)


def analyse(source: str | Path) -> BundleAnalysisResult:
    """Analyse a folder or zip bundle.

    Module-level convenience for the family's canonical call shape — equivalent
    to ``BundleAnalyser().analyse(source)``.
    """
    return analyse_bundle(source)


__all__ = [
    "BundleAnalyser",
    "BundleAnalysis",
    "BundleAnalysisResult",
    "analyse",
    "analyse_bundle",
    "MANIFEST",
    "__version__",
]
