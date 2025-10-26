# streamlit/app.py
import os
import time
import requests
import streamlit as st
from requests.auth import HTTPBasicAuth

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Rakuten Classifier", layout="centered")
st.title("Rakuten Product Classifier · Demo")

with st.sidebar:
    st.markdown("**API**: " + API)
    try:
        r = requests.get(f"{API}/healthz", timeout=3)
        st.success("API Healthy") if r.ok else st.error("API Unhealthy")
    except Exception as e:
        st.error(f"API Unreachable: {e}")

des = st.text_input("Designation")
desc = st.text_area("Description", height=120)
auth = HTTPBasicAuth("admin", "changeme")

col1, col2 = st.columns([1,1])
with col1:
    run = st.button("Predict")
with col2:
    clear = st.button("Clear")

if clear:
    st.experimental_rerun()

if run:
    if not des.strip():
        st.warning("Please input Designation")
    else:
        payload = {"designation": des.strip(), "description": desc or None}
        t0 = time.time()
        try:
            resp = requests.post(f"{API}/predict", json=payload, auth=auth, timeout=15)
            latency_ms = (time.time() - t0) * 1000
            if resp.ok:
                st.success(f"Prediction: {resp.json().get('prdtypecode')}")
                st.caption(f"Latency: {latency_ms:.1f} ms")
            else:
                st.error(f"HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")

#CI/CD Badge
owner = os.getenv("GH_OWNER", "your-gh-user")
repo  = os.getenv("GH_REPO",  "your-repo")
st.header("CI/CD Status")
st.markdown(f"**CI:** ![ci]("
            f"https://github.com/{owner}/{repo}/actions/workflows/ci.yaml/badge.svg)")
st.markdown(f"**Release:** ![release]("
            f"https://github.com/{owner}/{repo}/actions/workflows/release.yaml/badge.svg)")
st.caption(f"Repo: https://github.com/{owner}/{repo}")