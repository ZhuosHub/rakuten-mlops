import argparse
from pathlib import Path
import sqlite3
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.metrics import f1_score, classification_report
from sklearn.model_selection import train_test_split
from mlflow.tracking import MlflowClient


def read_train(db_path: str) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            "SELECT p.id, p.designation, p.description, y.prdtypecode "
            "FROM products p JOIN labels y ON p.id = y.id "
            "WHERE p.split='train';", con
        )
    finally:
        con.close()
    df["text"] = (df["designation"].fillna("") + " " + df["description"].fillna("")).str.strip()
    return df[["id","text","prdtypecode"]]

def build_pipeline(ngram=(1,2), min_df=2, max_features=None):
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=ngram, min_df=min_df, max_features=max_features)),
        ("clf", LinearSVC(class_weight="balanced"))
    ])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--mlflow-uri", default="file:./mlruns")
    ap.add_argument("--experiment", default="rakuten_text_baseline")
    ap.add_argument("--register", default="rakuten_clf")
    ap.add_argument("--test-size", type=float, default=0.1)
    ap.add_argument("--random-state", type=int, default=42)
    args = ap.parse_args()

    mlflow.set_tracking_uri(args.mlflow_uri)
    mlflow.set_experiment(args.experiment)

    df = read_train(args.db)

    # --- handle rare classes for stratified split ---
    counts = df["prdtypecode"].value_counts()
    kept_labels = counts[counts >= 2].index
    df_kept = df[df["prdtypecode"].isin(kept_labels)].copy()

    dropped_rows = len(df) - len(df_kept)
    n_classes_total = counts.size
    n_classes_kept = kept_labels.size

    # choose data for splitting
    use_stratified = len(df_kept) > 0 and df_kept["prdtypecode"].value_counts().min() >= 2
    df_split = df_kept if use_stratified else df

    with mlflow.start_run() as run:
        mlflow.log_metrics({
            "n_rows_total": len(df),
            "n_classes_total": int(n_classes_total),
            "dropped_singleton_rows": int(dropped_rows),
            "n_rows_after_drop": len(df_kept),
            "n_classes_after_drop": int(n_classes_kept),
        })
        mlflow.log_param("stratified_split", bool(use_stratified))

        if use_stratified:
            stratify_y = df_split["prdtypecode"]
        else:
            stratify_y = None  # fallback if stratification not possible

        X_train, X_val, y_train, y_val = train_test_split(
            df_split["text"],
            df_split["prdtypecode"],
            test_size=args.test_size,
            random_state=args.random_state,
            stratify=stratify_y
        )

        pipe = build_pipeline()
        pipe.fit(X_train, y_train)

        y_pred = pipe.predict(X_val)
        macro_f1 = f1_score(y_val, y_pred, average="macro")
        micro_f1 = f1_score(y_val, y_pred, average="micro")

        mlflow.log_params({
            "model": "LinearSVC",
            "vectorizer": "TfidfVectorizer",
            "ngram": "(1,2)",
            "min_df": 2,
            "max_features": None,
            "test_size": args.test_size
        })
        mlflow.log_metrics({"macro_f1": macro_f1, "micro_f1": micro_f1})

        report_path = Path("reports/figures"); report_path.mkdir(parents=True, exist_ok=True)
        (report_path / "val_report.txt").write_text(classification_report(y_val, y_pred), encoding="utf-8")
        mlflow.log_artifact(str(report_path / "val_report.txt"))

        mlflow.sklearn.log_model(pipe, artifact_path="model", registered_model_name=args.register)

    # ---- begin Phase-2 addition: compare vs previous and promote best ----
    mlflow.set_tracking_uri(args.mlflow_uri)
    client = MlflowClient()
    this_run_id = run.info.run_id

    # 1) find the version just registered by this run
    mvs = client.search_model_versions(f"name='{args.register}' and run_id='{this_run_id}'")
    v_this = max(int(v.version) for v in mvs) if mvs else None

    # 2) previous version = current version - 1
    prev_version = (v_this - 1) if (v_this is not None and v_this > 1) else None

    # 3) evaluate previous version (prefer macro_f1 tag; else load and score)
    macro_prev = None
    if prev_version is not None:
        try:
            full = client.get_model_version(name=args.register, version=int(prev_version))
            tag_val = full.tags.get("macro_f1")
            if tag_val is not None:
                try:
                    macro_prev = float(tag_val)
                except Exception:
                    macro_prev = None
            if macro_prev is None:
                prev_uri = f"models:/{args.register}/{int(prev_version)}"
                prev_model = mlflow.sklearn.load_model(prev_uri)
                y_prev = prev_model.predict(X_val)
                macro_prev = f1_score(y_val, y_prev, average="macro")
        except Exception:
            macro_prev = None  # safe fallback

    # 4) decide and tag current as best (tags only; no stages)
    promote = (macro_prev is None) or (macro_f1 >= macro_prev)
    if promote and v_this is not None:
        client.set_model_version_tag(args.register, int(v_this), "is_best", "true")
        client.set_model_version_tag(args.register, int(v_this), "macro_f1", f"{macro_f1:.4f}")
        # to Production stage
        client.set_registered_model_alias(
            name=args.register,
            alias="Production",
            version=int(v_this),
        )
    print(f"[model_selection] v_this={v_this}, prev_version={prev_version}, "
        f"this_macro={macro_f1:.4f}, prev_macro={macro_prev}, promote={promote}")

if __name__ == "__main__":
    main()
