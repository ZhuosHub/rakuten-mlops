# 📦 Rakuten MLOps — End-to-End Machine Learning Pipeline

This repository demonstrates a **complete, reproducible MLOps workflow** built around the *Rakuten Product Classification Challenge*, an e-commerce text classification task.

The goal is **not** to achieve state-of-the-art accuracy, but to design a **fully operational and transparent MLOps system** that covers the entire lifecycle:
> *from data → training → versioning → deployment → monitoring → presentation.*

---

## 🎯 1. Project Background and Objectives

### Background: Rakuten Product Classification
The **Rakuten France Product Classification Challenge** focuses on large-scale taxonomy prediction, where each product listing (title + description) must be assigned a `prdtypecode`, representing its category in Rakuten’s taxonomy.

### Why this matters
Accurate classification enables:
- better **search and recommendation systems**
- improved **catalog consistency**
- **automation** of manual labeling tasks at industrial scale

### Project Objectives
1. Build a **reproducible and logged training pipeline**
2. Implement **automatic model versioning** via MLflow Registry
3. Deploy a **secure inference API** (FastAPI)
4. Enable **automated retraining** (via cron job or Airflow)
5. Provide an **interactive Streamlit interface** for demo and presentation

---

## 🏗️ 2. System Architecture Overview

```mermaid
flowchart TD
  A[(SQLite Dataset)]:::data
  B[Training Script: train_model.py - scikit-learn]:::train
  C1[MLflow Tracking: metrics / params / artifacts]:::track
  C2[MLflow Model Registry: versions / aliases]:::registry
  C3[[Production Alias]]:::registry
  S1["FastAPI Service: /training & /predict (Basic Auth)"]:::serve
  U1[Streamlit App: presentation & demo]:::ui
  O1["cron: scheduled retraining (in API container)"]:::orchestrate
  A -->|read data| B
  B -->|log run| C1 -->|register| C2 --> C3
  O1 -->|call /training| S1 -->|trigger| B
  C3 -->|load for inference| S1 -->|predict result| U1
  U1 -.->|test & demo| S1
  classDef data        fill:#E3F2FD,stroke:#1E88E5,color:#0D47A1;
  classDef train       fill:#E8F5E9,stroke:#43A047,color:#1B5E20;
  classDef track       fill:#FFF8E1,stroke:#F9A825,color:#5D4037;
  classDef registry    fill:#FFE0B2,stroke:#FB8C00,color:#4E342E;
  classDef serve       fill:#F3E5F5,stroke:#8E24AA,color:#4A148C;
  classDef ui          fill:#E0F7FA,stroke:#00ACC1,color:#006064;
  classDef orchestrate fill:#FCE4EC,stroke:#D81B60,color:#880E4F;
