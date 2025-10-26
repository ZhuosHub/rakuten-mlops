import argparse
import sqlite3
from pathlib import Path
import pandas as pd

NEEDED = {"designation", "description", "productid", "imageid"}

def read_csv_simple(path: str) -> pd.DataFrame:
    # Standard comma-delimited UTF-8 CSV (from interim/)
    return pd.read_csv(path, encoding="utf-8", engine="c")

def ensure_needed(df: pd.DataFrame, source: str):
    have = set(df.columns)
    if not NEEDED.issubset(have):
        missing = NEEDED - have
        raise ValueError(f"{source} missing columns {missing}. got={sorted(have)}")

def load_csvs(x_train, y_train, x_test):
    xt = read_csv_simple(x_train)
    yt = read_csv_simple(y_train)
    xe = read_csv_simple(x_test)

    ensure_needed(xt, "X_train")
    ensure_needed(xe, "X_test")

    if "prdtypecode" not in yt.columns:
        raise ValueError(f"Y_train missing 'prdtypecode'. got={list(yt.columns)}")

    # Ensure id column exists; otherwise create from row index
    if "id" not in xt.columns: xt = xt.reset_index().rename(columns={"index": "id"})
    if "id" not in xe.columns: xe = xe.reset_index().rename(columns={"index": "id"})
    if "id" not in yt.columns: yt = yt.reset_index().rename(columns={"index": "id"})

    # Add split
    xt["split"] = "train"
    xe["split"] = "test"

    # Select & order columns
    xt = xt[["id", "designation", "description", "productid", "imageid", "split"]]
    xe = xe[["id", "designation", "description", "productid", "imageid", "split"]]
    yt = yt[["id", "prdtypecode"]]

    # ---- sanitize types (fixes sqlite 'datatype mismatch') ----
    # Coerce numeric ids and labels
    xt["id"] = pd.to_numeric(xt["id"], errors="coerce")
    xe["id"] = pd.to_numeric(xe["id"], errors="coerce")
    yt["id"] = pd.to_numeric(yt["id"], errors="coerce")
    yt["prdtypecode"] = pd.to_numeric(yt["prdtypecode"], errors="coerce")

    # Drop rows with NaN in required numeric fields
    xt = xt.dropna(subset=["id"]).copy()
    xe = xe.dropna(subset=["id"]).copy()
    yt = yt.dropna(subset=["id", "prdtypecode"]).copy()

    # Cast to plain Python int
    xt["id"] = xt["id"].astype(int)
    xe["id"] = xe["id"].astype(int)
    yt["id"] = yt["id"].astype(int)
    yt["prdtypecode"] = yt["prdtypecode"].astype(int)

    # Keep labels only for ids present in train
    train_ids = set(xt["id"].tolist())
    yt = yt[yt["id"].isin(train_ids)].copy()

    # Text fields: fill NaN and cast to str (sqlite-friendly)
    for df in (xt, xe):
        for c in ["designation", "description", "productid", "imageid", "split"]:
            df[c] = df[c].fillna("").astype(str)

    print(f"[sanitize] train={len(xt)}, test={len(xe)}, labels={len(yt)}")
    return xt, yt, xe

def write_sqlite(db_path, schema_sql, df_xt, df_yt, df_xe):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        with con:
            # Drop & recreate tables to avoid stale schema
            con.execute("DROP TABLE IF EXISTS products;")
            con.execute("DROP TABLE IF EXISTS labels;")

            schema = Path(schema_sql).read_text(encoding="utf-8")
            con.executescript(schema)

            # Quick schema check
            cols = [r[1] for r in con.execute("PRAGMA table_info(products);").fetchall()]
            required = {"id","designation","description","productid","imageid","split"}
            missing = required - set(cols)
            if missing:
                raise RuntimeError(f"Schema mismatch for 'products'. missing={missing}, got={cols}")

            # Insert
            df_xt.to_sql("products", con, if_exists="append", index=False)
            df_xe.to_sql("products", con, if_exists="append", index=False)
            df_yt.to_sql("labels",   con, if_exists="append", index=False)

            tr = con.execute("SELECT COUNT(*) FROM products WHERE split='train'").fetchone()[0]
            te = con.execute("SELECT COUNT(*) FROM products WHERE split='test'").fetchone()[0]
            lb = con.execute("SELECT COUNT(*) FROM labels").fetchone()[0]
            if lb != tr:
                raise RuntimeError(f"labels ({lb}) != train rows ({tr})")
            return tr, te, lb
    finally:
        con.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x-train", required=True)
    ap.add_argument("--y-train", required=True)
    ap.add_argument("--x-test",  required=True)
    ap.add_argument("--db",      default="data/processed/rakuten.db")
    ap.add_argument("--schema",  default="src/data/schema.sql")
    args = ap.parse_args()

    df_xt, df_yt, df_xe = load_csvs(args.x_train, args.y_train, args.x_test)
    tr, te, lb = write_sqlite(args.db, args.schema, df_xt, df_yt, df_xe)
    print(f"[OK] wrote to {args.db}\n  train={tr}, test={te}, labels={lb}")

if __name__ == "__main__":
    main()
