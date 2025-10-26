from functools import lru_cache
import os, joblib
from pathlib import Path
import mlflow
import mlflow.sklearn

# Two loading modes:
# 1) MLflow model registry version/stage: e.g. MODEL_URI="models:/rakuten_clf/Production"
# 2) Local artifact path: e.g. MODEL_URI="file:./mlruns/<exp_id>/<run_id>/artifacts/model"
MODEL_PATH = os.getenv("MODEL_PATH")
MODEL_URI = os.getenv("MODEL_URI", "models:/rakuten_clf@Production")
MLFLOW_URI = os.getenv("MLFLOW_URI", "file:./mlruns")

@lru_cache(maxsize=1)
def load_model():
    if MODEL_PATH and Path(MODEL_PATH).exists():
        return joblib.load(MODEL_PATH)
    mlflow.set_tracking_uri(MLFLOW_URI)
    return mlflow.sklearn.load_model(MODEL_URI)

def predict_one(designation: str, description: str | None):
    text = f"{designation or ''} {description or ''}".strip()
    model = load_model()
    pred = model.predict([text])[0]
    return int(pred)

def predict_batch(items):
    """
    items: list of dicts with keys {"designation": str, "description": str|None}
    """
    model = load_model()
    texts = [(i.get("designation","") + " " + (i.get("description") or "")).strip() for i in items]
    preds = model.predict(texts)
    return [int(p) for p in preds]
