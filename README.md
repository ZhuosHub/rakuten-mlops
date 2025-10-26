# 📦 Rakuten MLOps — End-to-End Pipeline 

This project demonstrates a full **MLOps workflow** using:

✅ FastAPI — training + inference  
✅ MLflow — experiment tracking + model registry (Production alias)  
✅ Cron — automated retraining  
✅ Streamlit — interactive demo + presentation  
✅ Docker Compose — orchestration  
✅ CI/CD via GitHub Actions  
✅ Optional: model export (`model.joblib`)  

---

##  0) Requirements

Make sure you have:

- Docker (Desktop) + Docker Compose  
- Git  
- **Git LFS (required if DB / model is tracked in LFS)**  

```bash
git lfs install  # only once
```

## 1) Clone & prepare
```bash
git clone <YOUR_REPO_URL> rakuten-mlops
cd rakuten-mlops

# pull any LFS assets (e.g., db/model files if present)
git lfs pull

# prepare environment file
cp .env.example .env
```

## 2) Start everything (clean rebuild)
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose ps
```

## 3) Sanity checks
```bash
# API health
curl -s http://localhost:8000/healthz
```

## 4) Training
Auto (cron)
Cron runs inside the API container.

If you want to set every 5 minutes for presentation:
```bash
docker compose exec api sh -lc '
printf "*/5 * * * * /usr/local/bin/daily_train.sh >> /var/log/cron.log 2>&1\n" | crontab - &&
service cron restart'
```

If you want to restore to daily at 02:00:
```bash
docker compose exec api sh -lc '
printf "0 2 * * * /usr/local/bin/daily_train.sh >> /var/log/cron.log 2>&1\n" | crontab - &&
service cron restart'
```

Check cron log (after it has run at least once):
```bash
docker compose exec api sh -lc 'tail -n 100 /var/log/cron.log'
```

