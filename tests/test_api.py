from fastapi.testclient import TestClient
from src.api.app import app
from src.api import app as app_module
import os

def test_healthz():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ok") is True

def test_predict_auth_and_payload(monkeypatch):
    monkeypatch.setattr(app_module, "API_USER", "u")
    monkeypatch.setattr(app_module, "API_PASS", "p")
    # Patch the module-level name actually used by the endpoint
    monkeypatch.setattr(app_module, "predict_one", lambda designation, description=None: 999)
    client = TestClient(app)
    r = client.post("/predict",
                    json={"designation": "abc", "description": "def"},
                    auth=("u", "p"))
    assert r.status_code == 200
    assert r.json() == {"prdtypecode": 999}

def test_predict_requires_auth(monkeypatch):
    monkeypatch.setattr(app_module, "predict_one",
                        lambda designation, description=None: 1)
    client = TestClient(app)
    r = client.post("/predict", json={"designation": "x"})
    assert r.status_code == 401
