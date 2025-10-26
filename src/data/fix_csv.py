import csv, re
from pathlib import Path
import argparse

DIGITS_ONLY = re.compile(r"[^0-9]")

def fix_x(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "r", encoding="utf-8-sig", newline="") as f_in, \
         open(dst, "w", encoding="utf-8", newline="") as f_out:
        reader = csv.reader(f_in)   # comma-delimited with proper quote handling
        writer = csv.writer(f_out)
        # canonical header
        writer.writerow(["id", "designation", "description", "productid", "imageid"])
        # skip original header
        try:
            next(reader)
        except StopIteration:
            return 0
        n = 0
        for row in reader:
            if not row:
                continue
            # keep only first 5 columns (pad if shorter)
            row = (row + ["", "", "", "", ""])[:5]

            # strip whitespace
            row = [c.strip() for c in row]

            # enforce digits-only for productid (col 3) and imageid (col 4)
            row[3] = DIGITS_ONLY.sub("", row[3])  # productid
            row[4] = DIGITS_ONLY.sub("", row[4])  # imageid

            writer.writerow(row)
            n += 1
    return n

def pass_through_y(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "r", encoding="utf-8-sig", newline="") as f_in, \
         open(dst, "w", encoding="utf-8", newline="") as f_out:
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        writer.writerow(["id", "prdtypecode"])
        try:
            next(reader)
        except StopIteration:
            return 0
        n = 0
        for row in reader:
            if not row:
                continue
            row = (row + [""])[:2]
            row = [c.strip() for c in row]
            row[0] = DIGITS_ONLY.sub("", row[0])  # id as digits
            row[1] = DIGITS_ONLY.sub("", row[1])  # prdtypecode as digits
            writer.writerow(row)
            n += 1
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x-train", required=True)
    ap.add_argument("--x-test", required=True)
    ap.add_argument("--y-train", required=True)
    ap.add_argument("--out-dir", default="data/interim")
    args = ap.parse_args()

    out = Path(args.out_dir)
    n1 = fix_x(Path(args.x_train), out / "X_train.csv")
    n2 = fix_x(Path(args.x_test),  out / "X_test.csv")
    n3 = pass_through_y(Path(args.y_train), out / "Y_train.csv")
    print(f"[OK] cleaned: X_train={n1} rows, X_test={n2} rows, Y_train={n3} rows → {out}")

if __name__ == "__main__":
    main()
