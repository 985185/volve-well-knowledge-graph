import pandas as pd
import re
from collections import Counter

IN_CSV = "out_wellkg_v3_catalog_v1.csv"
WHITELIST_CSV = "well_whitelist.csv"

TARGET_WELL = "15/9-F-12"   # change to another well later
TARGET_BUCKET = "WellTechnical_General"

STOP = set("""
the and for with from to of in on a an is are by rev version v0 v1 v2 final draft copy
pdf doc docx xls xlsx ppt pptx xml txt
15 9 f volve well data report reports
""".split())

def tokenize(s: str):
    s = s.lower()
    # keep only letters/numbers, turn separators into spaces
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    toks = [t for t in s.split() if len(t) >= 3 and t not in STOP]
    return toks

def bucket_row(row) -> str:
    top = (row.get("top_folder") or "").strip()
    tags = (row.get("tags") or "").strip()
    path = (row.get("path") or "").strip().lower()
    name = (row.get("name") or "").strip().lower()
    ext  = (row.get("ext_norm") or "").strip().lower()
    blob = " ".join([path, name, tags.lower(), top.lower()])

    if "ddr_xml" in tags.lower() or "div. reports" in path or "completionlog" in name or "completion log" in name:
        return "DDR"
    if top in {"Well_logs_pr_WELL", "Well_logs"}:
        return "Logs"
    if ext in {"las", "dlis", "lis"} or tags in {"LAS", "DLIS", "LIS"}:
        return "Logs"
    if top == "Well_technical_data" or "well_tech" in tags.lower() or "welltech" in blob:
        if ext == "wcd" or "wellcat" in blob:
            return "WellCat"
        if any(k in blob for k in ["survey", "trajectory", "directional", "gyro", "inclination", "azimuth", "dogleg"]):
            return "Survey_Trajectory"
        return "WellTechnical_General"
    return "Other"

def main():
    df = pd.read_csv(IN_CSV, dtype=str, low_memory=False).fillna("")
    wl = pd.read_csv(WHITELIST_CSV, dtype=str).fillna("")
    whitelist = set(wl["well_id"].str.strip())
    df = df[df["well_final"].str.strip().isin(whitelist)].copy()

    df["bucket"] = df.apply(bucket_row, axis=1)
    df = df[(df["well_final"] == TARGET_WELL) & (df["bucket"] == TARGET_BUCKET)].copy()

    print("Rows in bucket:", len(df))

    c = Counter()
    # Focus on filename + last path segment (usually informative)
    for _, r in df.iterrows():
        text = f"{r.get('name','')} {r.get('path','')}"
        c.update(tokenize(text))

    print("\nTop 60 tokens:")
    for tok, n in c.most_common(60):
        print(f"{tok:20s} {n}")

    # Also show sample filenames (first 40)
    print("\nSample names (first 40):")
    print(df["name"].head(40).to_string(index=False))

if __name__ == "__main__":
    main()