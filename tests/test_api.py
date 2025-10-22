import os
from fastapi.testclient import TestClient
from src.api.app import app

def test_healthz():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ok") is True

def test_predict_auth_and_payload(monkeypatch):
    os.environ["API_USER"] = "u"
    os.environ["API_PASS"] = "p"

    # mock prediction to avoid loading real model
    from src.models import predict_model
    monkeypatch.setattr(predict_model, "predict_one", lambda a,b: 999)

    client = TestClient(app)
    r = client.post("/predict", json={"designation":"abc","description":"def"},
                    auth=("u","p"))
    assert r.status_code == 200
    assert r.json() == {"prdtypecode": 999}
