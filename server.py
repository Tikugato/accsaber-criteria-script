"""
FastAPI server for Reloaded's Backend for live service of checking criteria.
"""
import io
import logging
import os
import tempfile
import zipfile
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from libs.Map import Map
from libs.CriteriaChecker import RunCriteriaChecks

app = FastAPI(title="AccSaber Criteria Checker")
log = logging.getLogger("uvicorn.error")


def find_mapset_root(extract_dir):
    for root, _dirs, files in os.walk(extract_dir):
        for f in files:
            if f.lower() == "info.dat":
                return root
    return None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/check")
async def check(
    zip: UploadFile = File(...),
    difficulty: str = Form(...),
    category: str = Form(...),
):
    zip_bytes = await zip.read()
    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="uploaded file is not a valid zip")

    with tempfile.TemporaryDirectory() as tmp:
        archive.extractall(tmp)
        mapset_root = find_mapset_root(tmp)
        if mapset_root is None:
            raise HTTPException(status_code=400, detail="Info.dat not found in uploaded zip")

        try:
            map_object = Map(mapset_root, difficulty, category)
            failures = RunCriteriaChecks(map_object)
        except Exception as exc:
            log.exception("criteria check failed for difficulty=%s category=%s", difficulty, category)
            raise HTTPException(status_code=500, detail=f"script error: {exc}")

    return {
        "status": "failed" if failures else "passed",
        "failures": failures or [],
    }
