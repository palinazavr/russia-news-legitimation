# =====================================================
# FULL AUDIT v2 of all 8 newspaper datasets:
#   eldiario, elmundo, magyar, polityka, rp, spiegel, telex, welt
#
# Fix vs v1: image_filename can contain MULTIPLE filenames joined by ";"
# (an article can have several images) -- v1 compared the whole joined
# string against the files on disk and wildly over-counted mismatches.
# This version splits on ";" (and strips whitespace) before comparing.
#
# Checks, per source:
#   - row count, duplicate article_url
#   - missing/empty title, text, date
#   - date parsing failures
#   - date window coverage (2022-02-24 00:00:00 -> 2026-06-10 23:59:59)
#   - image coverage: % rows with at least one image_filename
#   - individual image filenames referenced in CSV but missing on disk
#   - files present on disk but never referenced by any row (orphans)
#   - category value counts
#
# Run from 3.2_data_preprocessing (rp path is set explicitly below).
# =====================================================

import pandas as pd
from pathlib import Path

pd.set_option("display.width", 160)

WINDOW_START = pd.Timestamp("2022-02-24 00:00:00", tz="UTC")
WINDOW_END = pd.Timestamp("2026-06-10 23:59:59", tz="UTC")

SOURCES = {
    "eldiario": ("eldiario_final_data.csv", "eldiario_final_images"),
    "elmundo":  ("elmundo_final_data.csv", "elmundo_final_images"),
    "magyar":   ("magyar_final_data.csv", "magyar_final_images"),
    "polityka": ("polityka_final_data.csv", "polityka_final_images"),
    "rp":       ("rp_final_data_with_dates.csv",
                 "rp_final_images"),
    "spiegel":  ("spiegel_final_data.csv", "spiegel_final_images"),
    "telex":    ("telex_final_data.csv", "telex_final_images"),
    "welt":     ("welt_final_data.csv", "welt_final_images"),
}

REQUIRED_COLS = ["category", "article_url", "title", "date", "text"]


def split_filenames(cell):
    """image_filename can be one filename or several joined by ';'."""
    if pd.isna(cell):
        return []
    return [x.strip() for x in str(cell).split(";") if x.strip()]


summary_rows = []

for name, (csv_path, images_dir) in SOURCES.items():
    print("=" * 90)
    print(f"=== {name} ===")
    csv_path = Path(csv_path)
    images_dir = Path(images_dir)

    if not csv_path.exists():
        print(f"  !! CSV NOT FOUND: {csv_path}")
        summary_rows.append({"source": name, "status": "CSV_NOT_FOUND"})
        continue

    df = pd.read_csv(csv_path)
    n = len(df)
    print(f"  rows: {n}")

    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        print(f"  !! MISSING REQUIRED COLUMNS: {missing_cols}")

    dup_url = df["article_url"].duplicated().sum() if "article_url" in df.columns else None
    print(f"  duplicate article_url: {dup_url}")

    empty_title = (df["title"].fillna("").astype(str).str.strip() == "").sum() if "title" in df.columns else None
    empty_text = (df["text"].fillna("").astype(str).str.strip() == "").sum() if "text" in df.columns else None
    empty_date = df["date"].isna().sum() if "date" in df.columns else None
    print(f"  empty title: {empty_title} | empty text: {empty_text} | empty/NaN date: {empty_date}")

    if "date" in df.columns:
        dt = pd.to_datetime(df["date"], errors="coerce", utc=True, format="mixed")
        total_unparsed = dt.isna().sum()
        print(f"  date parse failures (including empty): {total_unparsed}")
        valid = dt.dropna()
        if len(valid):
            print(f"  date range found: {valid.min()}  ->  {valid.max()}")
            before_window = (valid < WINDOW_START).sum()
            after_window = (valid > WINDOW_END).sum()
            in_window = ((valid >= WINDOW_START) & (valid <= WINDOW_END)).sum()
            print(f"  before window (< 2022-02-24): {before_window}")
            print(f"  after window  (> 2026-06-10): {after_window}")
            print(f"  in window: {in_window} / {n}")
        else:
            before_window = after_window = in_window = None
            print("  no parseable dates at all!")
    else:
        total_unparsed = before_window = after_window = in_window = None

    if "category" in df.columns:
        print("  categories:")
        print(df["category"].value_counts().to_string())

    has_image_col = "image_filename" in df.columns
    if has_image_col:
        filenames_per_row = df["image_filename"].apply(split_filenames)
        with_image = (filenames_per_row.apply(len) > 0).sum()
        total_image_refs = filenames_per_row.apply(len).sum()
        print(f"  rows with >=1 image_filename: {with_image} / {n} ({with_image/n:.1%})")
        print(f"  total individual image references (after splitting ';'): {total_image_refs}")
    else:
        with_image = total_image_refs = None
        print("  !! no image_filename column")

    if images_dir.exists():
        files_on_disk = {f.name for f in images_dir.iterdir() if f.is_file()}
        print(f"  files physically in {images_dir}: {len(files_on_disk)}")

        if has_image_col:
            referenced = set()
            for lst in filenames_per_row:
                referenced.update(lst)
            missing_on_disk = referenced - files_on_disk
            orphans_on_disk = files_on_disk - referenced
            print(f"  individual filenames referenced in CSV but MISSING on disk: {len(missing_on_disk)}")
            if missing_on_disk:
                print(f"    examples: {list(missing_on_disk)[:8]}")
            print(f"  present on disk but NOT referenced in CSV (orphans): {len(orphans_on_disk)}")
        else:
            missing_on_disk = orphans_on_disk = None
    else:
        print(f"  !! IMAGES FOLDER NOT FOUND: {images_dir}")
        files_on_disk = missing_on_disk = orphans_on_disk = None

    summary_rows.append({
        "source": name,
        "rows": n,
        "dup_article_url": dup_url,
        "empty_title": empty_title,
        "empty_text": empty_text,
        "empty_date": empty_date,
        "date_unparsed": total_unparsed,
        "before_window": before_window,
        "after_window": after_window,
        "in_window": in_window,
        "rows_with_image": with_image,
        "image_pct": round(with_image / n, 4) if (with_image is not None and n) else None,
        "total_image_refs": total_image_refs,
        "files_on_disk": len(files_on_disk) if files_on_disk is not None else None,
        "csv_ref_missing_on_disk": len(missing_on_disk) if missing_on_disk is not None else None,
        "orphan_files_on_disk": len(orphans_on_disk) if orphans_on_disk is not None else None,
    })

print("\n\n" + "=" * 90)
print("=== SUMMARY ACROSS ALL 8 SOURCES ===")
summary_df = pd.DataFrame(summary_rows)
print(summary_df.to_string(index=False))

summary_df.to_csv("dataset_audit_summary_v2.csv", index=False, encoding="utf-8-sig")
print("\nsaved: dataset_audit_summary_v2.csv")

total_rows = summary_df["rows"].sum() if "rows" in summary_df else None
print(f"\nTOTAL ROWS ACROSS ALL SOURCES: {total_rows}")
