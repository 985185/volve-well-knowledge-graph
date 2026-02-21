# generate_manifests_v1_3.py
# Volve Well Dossier Generator (v1.3 - FINAL)
# - Lifecycle bucket structure
# - De-duplication by filename (path preference applied)
# - Strict foreign-well reference detection (no hallucinated IDs)
# - Supports both "11B" and "11 B" formats
# - Files only are foreign-flagged (directories ignored)

import json
import re
import shutil
from pathlib import Path

import pandas as pd

IN_CSV = "out_wellkg_v3_catalog_v1.csv"
WHITELIST_CSV = "well_whitelist.csv"
OUT_DIR = Path("wells")

# DDR HTML detection
DDR_HTML_RE = re.compile(
    r'15[_/ ]9[_/ -]?F[_/ -]?\d{1,2}[_-]\d{4}[_-]\d{2}[_-]\d{2}\.html$',
    re.IGNORECASE
)

# Strict well ID matcher
# Handles:
#   15_9-F-11B
#   15_9-F-11 B
#   15 9-F-11
WELL_TOKEN_RE = re.compile(
    r'(?<![A-Za-z0-9])'
    r'15[ _/ ]9[ _/ -]?F[ _/ -]?'
    r'(\d{1,2})'
    r'(?:\s*([A-Za-z]))?'     # optional single suffix letter (with or without space)
    r'(?![A-Za-z0-9-])',
    re.IGNORECASE
)

PREFERRED_BUCKET_ORDER = [
    "Well_Construction_Reports",
    "DDR_HTML",
    "DDR_PDF",
    "DDR_XML",
    "Logs",
    "WellCat",
    "Casing",
    "Cementing",
    "WellControl_Pressure",
    "Completion_Tubing",
    "Stress_Geomech",
    "Survey_Trajectory",
    "WellTechnical_General",
    "Other",
]

PREFERRED_PATH_SUBSTRINGS = [
    "/Well_logs_pr_WELL/",
    "/Well_logs/",
    "/Well_technical_data/",
]


def safe_folder_name(well_id: str) -> str:
    return well_id.replace("/", "_")


def canonicalize_well(num: str, suffix: str) -> str:
    suffix = (suffix or "").upper()
    return f"15/9-F-{num}{suffix}"


def extract_wells_from_text(text: str):
    if not text:
        return []

    found = []
    for m in WELL_TOKEN_RE.finditer(text):
        num = m.group(1)
        suf = m.group(2) or ""
        w = canonicalize_well(num, suf)

        if re.fullmatch(r"15/9-F-\d{1,2}[A-Za-z]?", w):
            if w not in found:
                found.append(w)

    return found


def any_kw(text: str, kws) -> bool:
    return any(k in text for k in kws)


def bucket_row(row) -> str:
    top = (row.get("top_folder") or "").strip()
    tags = (row.get("tags") or "").strip()
    path = (row.get("path") or "").strip()
    name = (row.get("name") or "").strip()
    ext = (row.get("ext_norm") or "").strip().lower()

    blob = " ".join([path.lower(), name.lower(), tags.lower(), top.lower()])

    if "ddr_xml" in tags.lower() or "daily drilling report - xml" in blob:
        return "DDR_XML"

    if ext == "html" and DDR_HTML_RE.search(name):
        return "DDR_HTML"

    if any_kw(blob, [
        "drilling_program",
        "drilling programme",
        "drilling program",
        "recommendation_to_drill",
        "recommendation to drill",
        "completion_report",
        "completion report",
        "completion log",
        "completionlog",
    ]):
        return "Well_Construction_Reports"

    if "div. reports" in blob or "drilling report" in blob or "daily drilling report" in blob:
        return "DDR_PDF"

    if top in {"Well_logs_pr_WELL", "Well_logs"}:
        return "Logs"

    if ext in {"las", "dlis", "lis"} or tags.strip().upper() in {"LAS", "DLIS", "LIS"}:
        return "Logs"

    if top == "Well_technical_data" or "well_tech" in tags.lower():
        if ext == "wcd" or "wellcat" in blob:
            return "WellCat"

        if any_kw(blob, ["survey", "trajectory", "directional", "gyro", "inclination", "azimuth", "dogleg"]):
            return "Survey_Trajectory"

        if any_kw(blob, ["casing", "csg", "liner", "shoe"]):
            return "Casing"

        if any_kw(blob, ["cement", "cbl", "vdl", "bond log"]):
            return "Cementing"

        if any_kw(blob, ["bop", "well control", "pressure test", "fit", "lot", "leak-off"]):
            return "WellControl_Pressure"

        if any_kw(blob, ["tubing", "packer", "xmas tree", "christmas tree", "perforat"]):
            return "Completion_Tubing"

        if any_kw(blob, ["stress", "geomech", "fracture gradient", "pore pressure"]):
            return "Stress_Geomech"

        return "WellTechnical_General"

    return "Other"


def bucket_sort_key(bucket: str) -> int:
    return PREFERRED_BUCKET_ORDER.index(bucket) if bucket in PREFERRED_BUCKET_ORDER else 999


def norm_filename(name: str, path: str) -> str:
    if name:
        return name.strip().lower()
    return Path(path).name.lower()


def path_preference_score(path: str) -> int:
    p = path.replace("\\", "/").lower()
    score = 0
    for i, sub in enumerate(PREFERRED_PATH_SUBSTRINGS):
        if sub.lower() in p:
            score += (len(PREFERRED_PATH_SUBSTRINGS) - i) * 10
    return score


def dedupe_items(items):
    best = {}
    for it in items:
        key = norm_filename(it.get("name", ""), it.get("path", ""))
        if not key:
            continue

        score = path_preference_score(it.get("path", ""))
        tie = len(it.get("path", "") or "")

        cur = best.get(key)
        if cur is None or (score, tie) > (cur["_score"], cur["_tie"]):
            it2 = dict(it)
            it2["_score"] = score
            it2["_tie"] = tie
            best[key] = it2

    out = []
    for v in best.values():
        v.pop("_score", None)
        v.pop("_tie", None)
        out.append(v)

    out.sort(key=lambda x: x.get("path", ""))
    return out


def main():
    df = pd.read_csv(IN_CSV, dtype=str, low_memory=False).fillna("")
    wl = pd.read_csv(WHITELIST_CSV, dtype=str).fillna("")
    whitelist = set(wl["well_id"].astype(str).str.strip())

    df = df[df["well_final"].astype(str).str.strip().isin(whitelist)].copy()
    df["bucket"] = df.apply(bucket_row, axis=1)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(exist_ok=True)

    wells = sorted(df["well_final"].unique())
    print("Wells to write:", len(wells))

    for well in wells:
        wdf = df[df["well_final"] == well].copy()
        well_dir = OUT_DIR / safe_folder_name(well)
        well_dir.mkdir(parents=True, exist_ok=True)

        buckets = {}
        for b, g in wdf.groupby("bucket"):
            items = g[["path", "name", "type", "ext_norm", "top_folder", "tags"]].to_dict(orient="records")

            for it in items:
                if (it.get("type") or "").lower() != "file":
                    it["foreign_ref_wells"] = []
                    continue

                text = f"{it.get('name','')} {it.get('path','')}"
                wells_found = extract_wells_from_text(text)
                it["foreign_ref_wells"] = [w for w in wells_found if w != well]

            items = dedupe_items(items)
            buckets[b] = items

        ordered = sorted(buckets.keys(), key=bucket_sort_key)

        with open(well_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump({
                "well": well,
                "counts": {k: len(v) for k, v in buckets.items()},
                "buckets": buckets,
            }, f, indent=2, ensure_ascii=False)

        with open(well_dir / "manifest.md", "w", encoding="utf-8") as f:
            f.write(f"# Well {well}\n\n")
            f.write("Well dossier manifest (v1.3): lifecycle buckets + dedupe + strict foreign-ref detection.\n\n")

            f.write("## Bucket summary\n\n")
            for k in ordered:
                f.write(f"- **{k}**: {len(buckets[k])}\n")
            f.write("\n")

            for k in ordered:
                f.write(f"## {k}\n\n")
                for item in buckets[k]:
                    line = f"- `{item['path']}`"
                    if item["foreign_ref_wells"]:
                        line += f" (foreign-ref: {', '.join(item['foreign_ref_wells'])})"
                    f.write(line + "\n")
                f.write("\n")

    print("Done. Wrote manifests into:", OUT_DIR.resolve())


if __name__ == "__main__":
    main()