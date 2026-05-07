from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from importlib.metadata import version
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from .core import analyse_bundle
from .models import BundleAnalysisResult

app = FastAPI(
    title="bundle-analyser",
    description="Analyse collections of files in folders or zip archives",
    version=version("bundle-analyser"),
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


class AnalyseRequest(BaseModel):
    path: str


@app.post("/analyse", response_model=BundleAnalysisResult)
def analyse(req: AnalyseRequest) -> BundleAnalysisResult:
    result = analyse_bundle(req.path)
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)
    return result


@app.post("/analyse/upload", response_model=BundleAnalysisResult)
async def analyse_upload(file: UploadFile = File(...)) -> BundleAnalysisResult:
    if not (file.filename or "").endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files supported for upload")
    tmp = Path(tempfile.mkdtemp())
    zip_path = tmp / (file.filename or "upload.zip")
    try:
        zip_path.write_bytes(await file.read())
        result = analyse_bundle(zip_path)
        if result.error:
            raise HTTPException(status_code=400, detail=result.error)
        return result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
