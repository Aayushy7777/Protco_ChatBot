from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.services.agent import register_dataframe
from app.services.profiler import profile_dataframe
from app.services.rag import ingest_file


router = APIRouter()


@router.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """
    Accept multiple CSV/XLSX files.
    For each file:
      - profile dataframe
      - register into agent store
      - ingest into Chroma
    """
    results: List[Dict[str, Any]] = []
    errors: List[str] = []

    Path(settings.UPLOAD_PATH).mkdir(parents=True, exist_ok=True)

    for f in files:
        filename = f.filename
        if not filename:
            errors.append("Unnamed file upload received.")
            continue

        suffix = Path(filename).suffix.lower()
        if suffix not in {".csv", ".xlsx", ".xls"}:
            errors.append(f"{filename}: only CSV and XLSX files are supported")
            continue

        try:
            raw_bytes = await f.read()
            save_path = Path(settings.UPLOAD_PATH) / filename
            save_path.write_bytes(raw_bytes)

            if suffix == ".csv":
                df = pd.read_csv(io.BytesIO(raw_bytes))
            else:
                df = pd.read_excel(io.BytesIO(raw_bytes))

            profile = profile_dataframe(df, filename=filename)
            register_dataframe(filename, df, profile)
            ingest_file(filename, df)

            auto = profile.get("auto_detected", {}) or {}
            numeric_cols = list((profile.get("numeric_columns") or {}).keys())
            categorical_cols = list((profile.get("categorical_columns") or {}).keys())
            date_cols = list((profile.get("date_columns") or {}).keys())

            results.append(
                {
                    "name": filename,
                    "rows": int(df.shape[0]),
                    "columns": int(df.shape[1]),
                    "profile": profile,
                    "auto_detected": auto,
                    "numeric_cols": numeric_cols,
                    "categorical_cols": categorical_cols,
                    "date_cols": date_cols,
                }
            )
        except Exception as e:
            errors.append(f"{filename}: {str(e)}")

    if errors and not results:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    return {"uploaded": results, "errors": errors}

