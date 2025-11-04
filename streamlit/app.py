# streamlit/presentation_app.py
import os
import time
import json
import requests
from requests.auth import HTTPBasicAuth
import streamlit as st

IMG_PATH = os.path.join(os.path.dirname(__file__), "workflow-mermaid.png")
RAKUTEN_IMG = os.path.join(os.path.dirname(__file__), "rakuten.png")
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
        "Goals and Objectives",
        "Project Status",
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
if page == "Goals and Objectives":
    st.title("Goals and Objectives of the Project")

    # --- 1) Background  ---
    st.markdown("## 1. Background: Rakuten Product Classification")
    col_left, col_right = st.columns([1.4, 1.0])
    with col_left:
        st.markdown(
            """
- **Task**: Large-scale taxonomy classification for e-commerce  
- **Input**: product **title** + **description**  
- **Output**: **prdtypecode** (category in Rakuten taxonomy)  
- **Scale**: ~99k examples, 1000+ classes (train/test split)  
- **Why it matters**:  
  - improves **search relevance**  
  - enhances **recommendations**  
  - enforces **catalog consistency**  
  - reduces **manual labeling** at scale  
            """
        )
    with col_right:
        st.image(RAKUTEN_IMG, caption="Rakuten Product Classification", use_container_width=True)

    st.markdown("---")

    # --- 2) ---
    st.markdown(
        """
## 2. Purpose of *this* project

Although the dataset comes from a real industrial challenge,  
the primary aim of this work is **not** to build a state-of-the-art classifier.  
Instead, the goal is to design a **complete, reproducible MLOps workflow** around it.

This project focuses on building:

- a transparent model lifecycle  
- automated retraining mechanisms  
- versioning and governance  
- deployable inference services  
- a clear demonstration interface

In other words, the classification task serves as the **application domain**,  
while the central learning outcome is the **construction of a stable MLOps pipeline**.

---

## 3. Core Objectives of the Project

### ✅ Objective 1 — Build a reproducible training workflow  
- deterministic or controlled randomness options  
- consistent data loading  
- logged metrics, parameters, and artifacts (MLflow)

### ✅ Objective 2 — Model versioning and governance  
- automatic comparison of new vs previous versions  
- promotion of the best version to the Production alias  
- transparent experiment history

### ✅ Objective 3 — Deploy an inference API  
- FastAPI endpoint for `/predict` and `/training`  
- includes Basic Authentication  
- uses the Production model from the registry

### ✅ Objective 4 — Automated retraining  
- cron-based scheduling inside the API container  
- fully automated logging and version updates  
- periodic evaluation and registry updates

### ✅ Objective 5 — Unified presentation interface  
- Streamlit as the central demo and narrative interface  
- exploration of versions, predictions, and workflow overview

---

## Summary

The project combines a real e-commerce classification problem  
with the construction of an end-to-end MLOps workflow.  
The focus is to demonstrate reproducibility, governance,  
automation, and deployment — the core skills of modern machine learning operations.
        """
    )



elif page == "Project Status":
    st.title("Current Status of the Project")

    st.markdown("""
The pipeline is **fully functional** and demonstrates the complete machine learning lifecycle.

### ✅ Current Capabilities
- **Automated hourly retraining (cron job)**  
  Every run is logged, evaluated, and versioned.
- **MLflow Tracking & Model Registry integration**  
  Metrics, parameters, artifacts, and model versions recorded in real time.
- **Automated model selection**  
  New model is compared with previous one; if better, it becomes the **Production** version.
- **FastAPI deployed inference service**  
  Protected with Bas      ic Auth and serving `/predict` and `/training` endpoints.
- **Streamlit demo application**  
  This interface shows the pipeline structure, training logs, model versions, and live predictions.

### ✅ The system now supports
- reproducible science  
- transparent model comparison  
- consistent deployment behaviour  
- real end-to-end demonstration

This page summarizes *what is already working* and what can be demonstrated live.
    """)


elif page == "Pipeline":
    st.header("End-to-End Workflow Diagram")
    col_img, col_txt = st.columns([1.6, 1.2])  
    with col_img:
        st.image(IMG_PATH, use_container_width=True, caption="MLOps Pipeline Overview")

    with col_txt:
        st.markdown("""
        ### Workflow Summary
        - **SQLite Database** → stores product texts and labels used for training.
        - **FastAPI Service** → exposes `/training` and `/predict` endpoints (with Basic Auth).
        - **Training Script** → logs metrics and models to **MLflow** and registers new versions.
        - **MLflow Model Registry** → promotes the best model to the **Production alias**.
        - **Cron Job** → automatically triggers retraining inside the API container.
        - **Streamlit App** → interacts with the API for both training and prediction demo.
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


    st.markdown("---")
    st.header("Next Steps and Possible Improvements")

    st.markdown("""
### 1. Expand the API layer
- Add endpoints for **model metrics**, **version info**, and **health monitoring**
- Integrate endpoints for **batch predictions** or **data upload**  
  (to support real-time feedback or human-in-the-loop retraining)

### 2. Replace cron with **Airflow orchestration**
- Use Airflow DAGs for retraining, validation, and deployment workflows  
- Enable **dependency tracking**, **scheduling**, and **error recovery**
- Store logs and metrics directly in a **central Airflow UI**

### 3. Enhance model evaluation
- Add **drift detection** and **alerting** (e.g., Prometheus + Grafana)
- Introduce **minimum performance thresholds** for model promotion
- Automate rollback to previous Production version if performance drops

### 4. Improve scalability and reliability
- Deploy API using **Kubernetes** for auto-scaling and load balancing
- Use **message queues** (RabbitMQ / Kafka) for asynchronous prediction
- Store data in **PostgreSQL** instead of SQLite for concurrent access

### 5. Extend the demo and frontend
- Add **data visualization** of model performance trends  
- Integrate **interactive error analysis** and **prediction explanations (SHAP)**
    """)
    st.markdown("---")
    st.success("Ready for defense. Questions welcome.")