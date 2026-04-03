from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from services.csv_processor import clean_data, detect_schema, load_csv
from services.vector_store import VectorStoreService
from utils.state import STATE, set_dataset


router = APIRouter()
vector_store = VectorStoreService()


@router.post("/upload")
async def upload(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    uploaded = []
    schemas: Dict[str, Dict[str, Any]] = {}
    errors = []
    os.makedirs("../data", exist_ok=True)

    for f in files:
        try:
            if not f.filename.lower().endswith(".csv"):
                errors.append({"file": f.filename, "error": "Only CSV files are supported."})
                continue
            local = Path("../data") / f"{uuid.uuid4().hex}_{f.filename}"
            content = await f.read()
            local.write_bytes(content)
            df = load_csv(str(local))
            schema = detect_schema(df)
            set_dataset(f.filename, df, schema)
            rows_text = [jsonable_row(r) for r in df.head(200).to_dict(orient="records")]
            vector_store.store_data(f.filename, rows_text)
            uploaded.append(f.filename)
            schemas[f.filename] = schema
        except Exception as e:
            errors.append({"file": f.filename, "error": str(e)})

    return {"uploaded_files": uploaded, "schemas": schemas, "errors": errors}


def jsonable_row(row: Dict[str, Any]) -> str:
    out = {}
    for k, v in row.items():
        if isinstance(v, (pd.Timestamp,)):
            out[k] = str(v)
        else:
            out[k] = v
    return str(out)

