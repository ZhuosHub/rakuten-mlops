# streamlit/presentation_app.py
import os
import time
import json
import requests
from requests.auth import HTTPBasicAuth
import streamlit as st

# --------- Config from env ---------
API = os.getenv("API_URL", "http://localhost:8000")
API_USER = os.getenv("API_USER", "admin")
API_PASS = os.getenv("API_PASS", "changeme")

GH_OWNER = os.getenv("GH_OWNER", "")
GH_REPO = os.getenv("GH_REPO",  "")
GH_TOKEN = os.getenv("GH_TOKEN")  # optional; for last-run API

MLFLOW_URL = os.getenv("MLFLOW_URL", "http://localhost:5000")

auth = HTTPBasicAuth(API_USER, API_PASS)
headers_json = {"Content-Type": "application/json"}

# --------- Small helpers ----------
def get(url, **kw):
    return requests.get(url, auth=auth, timeout=15, **kw)

def post(url, **kw):
    return requests.post(url, auth=auth, timeout=60, **kw)

def ping_api():
    try:
        r = get(f"{API}/healthz")
        return r.ok
    except Exception:
        return False

def format_json(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2)

# --------- Sidebar nav ------------
st.set_page_config(page_title="Rakuten · MLOps Presentation", layout="wide")
st.sidebar.title("MLOps Presentation")
page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Pipeline",
        "Live Training",
        "Live Prediction",
        "CI/CD Status",
        "MLflow & Ops",
        "Summary",
    ],
    index=0,
)

with st.sidebar:
    st.markdown(f"**API:** `{API}`")
    st.markdown(f"**Auth:** `{API_USER}/********`")
    st.markdown("**API health:** " + ("OK" if ping_api() else "DOWN"))

# --------- Pages -------------------
if page == "Overview":
    st.title("Rakuten Product Classification — End-to-End MLOps")
    st.markdown("""
**Goal**: Build a reproducible pipeline from training → versioning → deployment → demo.
**Scope**:
- FastAPI: `/training`, `/predict`, `/healthz`
- MLflow: Tracking + Model Registry (Production alias)
- Cron: Automated retraining (every 5 min for demo)
- Streamlit: This presentation + live demo
- Docker Compose: Orchestration (mlflow / api / streamlit)
    """)

    col1, col2 = st.columns([1,1])
    with col1:
        st.subheader("Key Features")
        st.markdown("""
- Manual & automated training
- MLflow versioning + Production alias
- Deployed inference via FastAPI
- Streamlit interactive demo
        """)
    with col2:
        st.subheader("What you will see")
        st.markdown("""
- New versions appearing in MLflow
- (If better) auto-promotion to **Production**
- Live prediction from the UI
        """)

elif page == "Pipeline":
    st.header("System Pipeline (High-Level)")
    st.markdown("""
1. **Cron** → calls FastAPI **`/training`**
2. **Training script** → logs to **MLflow**, registers version, compares metrics, updates **Production** alias
3. **FastAPI `/predict`** → loads **Production** (or file fallback) and returns predictions
4. **Streamlit** → interactive UI calling `/predict`
    """)
    st.markdown("---")
    st.subheader("Quick Health Checks")
    col1, col2, col3 = st.columns(3)
    with col1:
        ok = ping_api()
        st.metric("API", "UP" if ok else "DOWN")
        if st.button("Check /healthz"):
            try:
                r = get(f"{API}/healthz")
                st.code(format_json(r.json()))
            except Exception as e:
                st.error(str(e))
    with col2:
        st.write("MLflow UI")
        st.markdown(f"[Open MLflow]({MLFLOW_URL})")
    with col3:
        st.write("Cron (server-side)")
        st.caption("Logs live under `/var/log/cron.log` inside API container.")

elif page == "Live Training":
    st.header("Trigger Training (via FastAPI `/training`)")
    st.caption("This will run the training script, log to MLflow and create a new model version.")
    if st.button("Run training now"):
        t0 = time.time()
        try:
            r = post(f"{API}/training", headers=headers_json)
            dt = time.time() - t0
            if r.ok:
                st.success(f"Triggered. Latency {dt:.2f}s")
                payload = r.json()
                st.subheader("Response")
                st.code(format_json(payload))
                if "stdout" in payload and payload["stdout"]:
                    with st.expander("stdout"):
                        st.code(payload["stdout"])
                if "stderr" in payload and payload["stderr"]:
                    with st.expander("stderr"):
                        st.code(payload["stderr"])
            else:
                st.error(f"HTTP {r.status_code}")
                st.code(r.text)
        except Exception as e:
            st.error(f"Failed: {e}")

    st.divider()
    st.subheader("Cron (Auto-Retraining)")
    st.markdown("""
- For demo: scheduled every **5 minutes**
- Evidence: MLflow shows **new versions** appearing periodically
- In production: change to daily schedule
    """)
    st.markdown(f"[Open MLflow to verify versions →]({MLFLOW_URL})")

elif page == "Live Prediction":
    st.header("Predict Product Type Code (FastAPI `/predict`)")
    with st.form("predict_form"):
        designation = st.text_input("Designation (required)")
        description = st.text_area("Description (optional)", height=120)
        submitted = st.form_submit_button("Predict")
    if submitted:
        if not designation.strip():
            st.warning("Please input designation.")
        else:
            payload = {"designation": designation.strip(), "description": description or None}
            t0 = time.time()
            try:
                r = post(f"{API}/predict", json=payload, headers=headers_json)
                dt = (time.time() - t0) * 1000
                if r.ok:
                    st.success(f"Prediction: {r.json().get('prdtypecode')}")
                    st.caption(f"Latency: {dt:.1f} ms")
                    st.code(format_json(r.json()))
                else:
                    st.error(f"HTTP {r.status_code}")
                    st.code(r.text)
            except Exception as e:
                st.error(f"Request failed: {e}")

elif page == "CI/CD Status":
    st.header("CI/CD — GitHub Actions")
    if GH_OWNER and GH_REPO:
        st.markdown(f"**CI:** ![ci](https://github.com/{GH_OWNER}/{GH_REPO}/actions/workflows/ci.yaml/badge.svg)")
        st.markdown(f"**Release:** ![release](https://github.com/{GH_OWNER}/{GH_REPO}/actions/workflows/release.yaml/badge.svg)")
        st.caption(f"Repository: https://github.com/{GH_OWNER}/{GH_REPO}")

        st.subheader("Latest Runs")
        try:
            headers = {"Accept": "application/vnd.github+json"}
            if GH_TOKEN:
                headers["Authorization"] = f"Bearer {GH_TOKEN}"

            def last_run(workflow):
                url = f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/actions/workflows/{workflow}/runs?per_page=1"
                resp = requests.get(url, headers=headers, timeout=10).json()
                return resp["workflow_runs"][0] if resp.get("workflow_runs") else None

            for wf in ("ci.yaml", "release.yaml"):
                run = last_run(wf)
                if run:
                    st.write(f"**{wf}** → `{run['conclusion'] or run['status']}` · [{run['html_url']}]({run['html_url']})")
                else:
                    st.write(f"**{wf}** → No runs.")
        except Exception as e:
            st.warning(f"Could not query GitHub API: {e}")
    else:
        st.info("Set GH_OWNER and GH_REPO env vars to display badges and latest runs.")

elif page == "MLflow & Ops":
    st.header("MLflow Quick Links")
    st.markdown(f"- **MLflow UI**: {MLFLOW_URL}")
    st.markdown("- Model: `rakuten_clf` → check **Aliases** column for `Production`")
    st.divider()
    st.subheader("Ops Notes")
    st.markdown("""
- **Cron** runs inside API container, calls `/training`
- **Model selection**: macro-F1 comparison vs previous
- **Production alias** points to the best-known version
- **MODEL_PATH** file fallback supported for inference
    """)

elif page == "Summary":
    st.header("What’s Done")
    st.markdown("""
- End-to-end pipeline: training → registry → deployment → demo
- Automated retraining via cron (5-min for demo)
- MLflow Model Registry with **Production** alias
- FastAPI inference + Streamlit front-end
    """)
    st.success("Ready for defense. Questions welcome.")
