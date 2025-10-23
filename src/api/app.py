import os
from pydantic import BaseModel
import subprocess
from typing import List, Optional
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi import Depends

from src.models.predict_model import predict_one, predict_batch

app = FastAPI(title="Rakuten Product Classifier")

# --- Phase 3: Basic Auth ---
security = HTTPBasic()
API_USER = os.getenv("API_USER", "admin")
API_PASS = os.getenv("API_PASS", "changeme")

def require_auth(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, API_USER)
    ok_pass = secrets.compare_digest(credentials.password, API_PASS)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return True
# ----------------------------

class PredictIn(BaseModel):
    designation: str
    description: Optional[str] = None

class PredictBatchIn(BaseModel):
    items: List[PredictIn]

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/predict")
def predict(inp: PredictIn, _: bool = Depends(require_auth)):
    code = predict_one(inp.designation, inp.description)
    return {"prdtypecode": code}

@app.post("/predict_batch")
def predict_many(inp: PredictBatchIn, _: bool = Depends(require_auth)):
    preds = predict_batch([i.dict() for i in inp.items])
    return {"prdtypecodes": preds}

@app.post("/training")
def training(_: bool = Depends(require_auth)):
    """
    Synchronous training trigger. Simple.
    """
    db = os.getenv("DB_PATH", "data/processed/rakuten.db")
    mlflow_uri = os.getenv("MLFLOW_URI", "file:./mlruns")
    experiment = os.getenv("EXPERIMENT", "rakuten_text_baseline")
    register = os.getenv("REGISTER_NAME", "rakuten_clf")

    cmd = [
        "python", "src/models/train_model.py",
        "--db", db,
        "--mlflow-uri", mlflow_uri,
        "--experiment", experiment,
        "--register", register
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    ok = (result.returncode == 0)
    return {
        "ok": ok,
        "stdout": result.stdout[-2000:],  # tail to keep response short
        "stderr": result.stderr[-2000:]
    }
