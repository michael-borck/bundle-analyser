from pydantic import BaseModel


class FileResult(BaseModel):
    file: str          # relative path within the bundle
    analyser: str | None  # which analyser handled it, None if unrecognised
    result: dict | None   # the analysis result, None on error or unrecognised
    error: str | None     # error message if analysis failed


class BundleAnalysisResult(BaseModel):
    source: str                        # original path or "upload"
    source_type: str                   # "folder" or "zip"
    total_files: int
    analysed_files: int
    unrecognised_files: list[str]
    errors: list[str]
    file_type_distribution: dict[str, int]  # extension → count (e.g. {"pdf": 3, "docx": 1})
    results: list[FileResult]
    error: str | None = None           # top-level error (bad input etc.)
