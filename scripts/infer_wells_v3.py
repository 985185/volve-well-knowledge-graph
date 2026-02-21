import re
import pandas as pd

CSV_PATH = "volve_data_meta.csv"
OUT_PREFIX = "out_wellkg_v3"

EXCLUDE_TOP_FOLDERS = {"PI System Manager Sleipner"}

# Canonical well id: 15/9-F-<num><optional letter>
CANON_RE = re.compile(r'^15/9-F-\d{1,2}[A-Za-z]?$')

# Strict well token (many variants) for generic scan
WELL_TOKEN_RE = re.compile(
    r'(15[ _/\\]9[ _-]?F[ _-]?\d{1,2}(?:[ _]?[A-Za-z])?)',
    re.IGNORECASE
)

def canonicalize(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip().replace("\\", "/")
    s = re.sub(r'^15[ _]9', '15/9', s)               # 15_9 -> 15/9
    s = re.sub(r'[ _-]?F[ _-]?', 'F-', s)            # F -> F-
    s = s.replace("15/9F-", "15/9-F-")               # fix missing hyphen
    s = re.sub(r'-{2,}', '-', s)                     # collapse --
    s = re.sub(r'(15/9-F-\d{1,2})[ _]([A-Za-z])$', r'\1\2', s)  # join suffix
    s = re.sub(r'(15/9-F-\d{1,2})([a-z])$', lambda m: m.group(1)+m.group(2).upper(), s)
    return s

def is_valid(w: str) -> bool:
    return bool(CANON_RE.fullmatch(w))

def infer_from_segments(path: str) -> str:
    """Segment-aware: look for folder segments that are exactly a well-ish token."""
    if not isinstance(path, str) or not path:
        return ""
    parts = [p for p in path.replace("\\", "/").split("/") if p]
    # scan each segment
    for seg in parts:
        m = WELL_TOKEN_RE.fullmatch(seg.strip())
        if m:
            w = canonicalize(m.group(1))
            if is_valid(w):
                return w
    return ""

def infer_generic(path: str) -> str:
    """Fallback generic scan anywhere in string."""
    if not isinstance(path, str) or not path:
        return ""
    m = WELL_TOKEN_RE.search(path)
    if not m:
        return ""
    w = canonicalize(m.group(1))
    return w if is_valid(w) else ""

def infer_well(path: str, top_folder: str) -> str:
    # 1) Segment-based inference works well for well-folder structures
    w = infer_from_segments(path)
    if w:
        return w

    # 2) Folder-specific patterns (tight, not broad)
    p = path.replace("\\", "/")

    # Well_logs_pr_WELL/<well folder>/...
    if top_folder == "Well_logs_pr_WELL":
        m = re.search(r'/Well_logs_pr_WELL/([^/]+)/', p, re.IGNORECASE)
        if m:
            w2 = canonicalize(m.group(1))
            if is_valid(w2):
                return w2

    # Well_logs/.../<well folder>/...
    if top_folder == "Well_logs":
        m = re.search(r'/Well_logs/[^/]+/([^/]+)/', p, re.IGNORECASE)
        if m:
            w2 = canonicalize(m.group(1))
            if is_valid(w2):
                return w2

    # Well_technical_data often has .../15_9-F-9/... inside path
    if top_folder == "Well_technical_data":
        w3 = infer_generic(p)
        if w3:
            return w3

    # WITSML paths might contain wells as segments or embedded; try generic
    if top_folder == "WITSML Realtime drilling data":
        w4 = infer_generic(p)
        if w4:
            return w4

    # Seismic / RMS / others: generic if present
    return infer_generic(p)

def main():
    df = pd.read_csv(CSV_PATH, dtype=str, low_memory=False)
    for c in ["path", "top_folder", "tags", "well", "name", "type", "ext_norm"]:
        df[c] = df[c].fillna("").astype(str)

    df = df[~df["top_folder"].isin(EXCLUDE_TOP_FOLDERS)].copy()

    # canonicalize existing well column
    df["well_existing"] = df["well"].str.strip()
    df["well_existing_canon"] = df["well_existing"].apply(canonicalize)
    df.loc[~df["well_existing_canon"].apply(is_valid), "well_existing_canon"] = ""

    # infer
    df["well_inferred"] = df.apply(lambda r: infer_well(r["path"], r["top_folder"]), axis=1)

    # final preference: inferred then existing
    df["well_final"] = df["well_inferred"]
    df.loc[(df["well_final"] == "") & (df["well_existing_canon"] != ""), "well_final"] = df["well_existing_canon"]

    total = len(df)
    bound = (df["well_final"] != "").sum()
    print("\n=== V3 SCOPE (PI excluded) ===")
    print("Rows:", total)
    print("Bound:", bound)
    print("Unbound:", total - bound)
    print("Bind rate:", f"{bound/total:.2%}")

    print("\n=== TOP WELLS ===")
    print(df.loc[df["well_final"] != "", "well_final"].value_counts().head(30).to_string())

    print("\n=== BIND RATE BY TOP_FOLDER ===")
    by = df.groupby("top_folder").apply(lambda g: (g["well_final"] != "").mean()).sort_values(ascending=False)
    print((by * 100).round(2).to_string())

    out_csv = f"{OUT_PREFIX}_catalog_v1.csv"
    keep_cols = ["path", "name", "type", "ext_norm", "top_folder", "tags",
                 "well_existing", "well_existing_canon", "well_inferred", "well_final"]
    df[keep_cols].to_csv(out_csv, index=False)
    print("\nWrote:", out_csv)

if __name__ == "__main__":
    main()