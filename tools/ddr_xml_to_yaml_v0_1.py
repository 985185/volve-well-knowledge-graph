# =========================
# Volve DDR XML -> YAML + Validation (v0.1)
# TJ - final runnable Colab cell
# =========================

from google.colab import drive
drive.mount('/content/drive')

import os, glob, re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

# PyYAML
try:
    import yaml
except ImportError:
    !pip -q install pyyaml
    import yaml

# -------------------------
# CONFIG (change only this)
# -------------------------
BASE_DIR = "/content/drive/MyDrive/15_9_F_11_B"
XML_DIR  = BASE_DIR                           # XML files live here
GEN_DIR  = os.path.join(BASE_DIR, "generated_yaml")
GT_PATH  = os.path.join(BASE_DIR, "ground_truth.fixed.yaml")

# -------------------------
# Helpers
# -------------------------
def _text(el):
    if el is None or el.text is None:
        return None
    t = el.text.strip()
    return t if t else None

def find_first_text(root, endswith_tags):
    for el in root.iter():
        tag = el.tag.lower()
        for s in endswith_tags:
            if tag.endswith(s.lower()):
                t = _text(el)
                if t:
                    return t
    return None

def parse_date_from_filename(fn):
    m = re.search(r"_(\d{4})_(\d{2})_(\d{2})\.", fn)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

def shift_date_minus_1(d):
    if not d:
        return "unknown"
    dt = datetime.strptime(d, "%Y-%m-%d") - timedelta(days=1)
    return dt.strftime("%Y-%m-%d")

def parse_depths_from_summary(summary):
    """
    Extract depth_start_md and depth_end_md from common DDR phrases.
    Handles:
      - from X m MD to Y m MD
      - to section TD at Z m
      - RIH casing to Z m
      - washed down to Z m
    """
    s = summary or ""

    m = re.search(r"from\s+(\d+(\.\d+)?)\s*m\s*MD\s*to\s+(\d+(\.\d+)?)\s*m\s*MD", s, re.IGNORECASE)
    if m:
        return float(m.group(1)), float(m.group(3))

    m = re.search(r"to\s+section\s+TD\s+at\s+(\d+(\.\d+)?)\s*m", s, re.IGNORECASE)
    if m:
        return None, float(m.group(1))

    m = re.search(r"(?:rih|run).*casing.*?\bto\s+(\d+(\.\d+)?)\s*m", s, re.IGNORECASE)
    if m:
        return None, float(m.group(1))

    m = re.search(r"washed\s+down\s+to\s+(\d+(\.\d+)?)\s*m", s, re.IGNORECASE)
    if m:
        return None, float(m.group(1))

    m = re.search(r"\bto\s+(\d+(\.\d+)?)\s*m\b", s, re.IGNORECASE)
    if m:
        return None, float(m.group(1))

    return None, None

def infer_operation(summary):
    """
    Keyword-based (deterministic) operation inference.
    ORDER MATTERS.
    """
    blob = (summary or "").lower()

    # casing / wellhead ops
    if "wearbushing" in blob or "wear bushing" in blob:
        return "retrieve_wear_bushing"
    if "washed bop" in blob or "washed wellhead" in blob or "bop cavities" in blob:
        return "wash_bop_wellhead"
    if "casing" in blob and ("rih" in blob or "run" in blob):
        return "run_casing"
    if "cement" in blob:
        return "cement"
    if "woc" in blob:
        return "woc"
    if "bop test" in blob:
        return "test_bop"
    if "choke drill" in blob:
        return "choke_drill"

    # drilling ops
    if "washed/reamed" in blob or "washed / reamed" in blob or "ream" in blob:
        return "ream"
    if "orientated" in blob or "orient" in blob:
        return "orient"
    if "drill" in blob:
        return "drill"

    # trips
    if "pooh" in blob or "poh" in blob or "trip out" in blob:
        return "trip_out"
    if "rih" in blob or "trip in" in blob:
        return "trip_in"

    return "other"

def infer_verifications(summary):
    blob = (summary or "").lower()
    v = []
    if "flowcheck" in blob or "flowchecked" in blob or "well static" in blob:
        v.append("well_static_flowcheck")
    if "to section td" in blob:
        v.append("td_survey")
    if "gyro" in blob:
        v.append("gyro_confirmation")
    if "no backflow" in blob:
        v.append("cement_displacement_confirmed")
    if "float" in blob:
        v.append("casing_float_verified")
    return v if v else None

def infer_issue(summary):
    blob = (summary or "").lower()
    if "hydraulic leak" in blob:
        return "hydraulic_leak"
    if "hts failure" in blob or "unable to function hts" in blob:
        return "mechanical_failure"
    if "tool" in blob:
        return "tool_failure"
    return "none"

def extract_rig_name(root):
    # Try nameRig
    rig = find_first_text(root, ["nameRig"])
    if rig and rig.lower() not in ["true", "false"]:
        return rig

    # Try rigAlias/name pattern
    for el in root.iter():
        if el.tag.lower().endswith("rigalias"):
            for child in el:
                if child.tag.lower().endswith("name"):
                    t = _text(child)
                    if t and t.lower() not in ["true", "false"]:
                        return t

    # Last resort: any tag containing rig
    for el in root.iter():
        if "rig" in el.tag.lower():
            t = _text(el)
            if t and t.lower() not in ["true", "false"]:
                return t

    return "unknown"

def xml_to_yaml_doc(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    fn = os.path.basename(xml_path)

    # Date: filename date - 1 day to match ops window
    d = parse_date_from_filename(fn)
    date = shift_date_minus_1(d) if d else "unknown"

    wellbore = find_first_text(root, ["nameWellbore"]) or "unknown"
    wellbore = wellbore.replace("NO ", "").strip()

    operator = (find_first_text(root, ["nameOperator"]) or
                find_first_text(root, ["operator"]) or "unknown")

    spud = find_first_text(root, ["dTimSpud"])
    spud_date = spud[:10] if spud else "unknown"

    dia = find_first_text(root, ["diaHole"])
    hole_size_in = 12.25
    if dia:
        try:
            hole_size_in = float(dia)
        except:
            pass

    md_text = find_first_text(root, ["md"])
    depth_end_md = None
    if md_text:
        try:
            depth_end_md = float(md_text)
        except:
            pass

    summary = (find_first_text(root, ["sum24Hr"]) or
               find_first_text(root, ["summary"]) or "").strip()

    depth_start_md, depth_from_summary_end = parse_depths_from_summary(summary)
    if depth_from_summary_end is not None:
        depth_end_md = depth_from_summary_end

    op = infer_operation(summary)
    verif = infer_verifications(summary)
    issue = infer_issue(summary)
    rig = extract_rig_name(root)

    doc = {
        "schema_version": "0.1",
        "well": {
            "name": wellbore,
            "operator": operator,
            "rig": rig,
            "spud_date": spud_date,
            "hpht": True,
            "tight_well": True,
            "water_depth_m": 91,
            "rkb_msl_m": 54.9,
        },
        "section": {
            "hole_size_in": hole_size_in,
            "name": "Auto-generated from DDR XML",
            "planned_td_md": None,
        },
        "fluid_program": {
            "mud_system": None,
            "mud_density_sg": None,
            "ecd_sg": None,
            "emw_sg": None,
        },
        "context_notes": "Auto-generated from DDR XML (deterministic v0.1; date shifted -1 day).",
        "events": [
            {
                "date": date,
                "operation": op,
                "depth_start_md": depth_start_md,
                "depth_end_md": depth_end_md,
                "start_time": None,
                "end_time": None,
                "summary": summary,
                "avg_rop_mph": None,
                "inclination_deg": None,
                "azimuth_deg": None,
                "formation": "unknown",
                "issue": issue,
                "issue_note": None,
                "decision": None,
                "verification": verif,
                "sources": [{"file": fn, "page": 1, "quote_snippet": None}],
            }
        ],
    }
    return doc

# -------------------------
# 1) Generate YAML files
# -------------------------
os.makedirs(GEN_DIR, exist_ok=True)
xml_files = sorted(glob.glob(os.path.join(XML_DIR, "*.xml")))

print("XML files found:", len(xml_files))
print("GEN_DIR:", GEN_DIR)
print("GT_PATH:", GT_PATH)

if len(xml_files) == 0:
    raise RuntimeError("No XML files found. Check BASE_DIR/XML_DIR.")

written = []
for x in xml_files:
    out_name = os.path.splitext(os.path.basename(x))[0] + ".generated.yaml"
    out_path = os.path.join(GEN_DIR, out_name)
    doc = xml_to_yaml_doc(x)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True)
    written.append(out_path)

print("Generated YAML files:", len(written))
print("Example:", written[0])

# -------------------------
# 2) Compare to Ground Truth
# -------------------------
if not os.path.exists(GT_PATH):
    raise RuntimeError("Ground truth file not found at GT_PATH. Ensure ground_truth.fixed.yaml exists.")

gt = yaml.safe_load(Path(GT_PATH).read_text(encoding="utf-8"))
gt_events = {ev["date"]: ev for ev in gt.get("events", [])}

gen_files = sorted(glob.glob(os.path.join(GEN_DIR, "*.generated.yaml")))

print("\n" + "=" * 70)
print("VALIDATION REPORT")
print("=" * 70)
print("Ground truth events:", len(gt_events))
print("Generated files:", len(gen_files))

op_correct = 0
depth_correct = 0
verif_total = 0
verif_match = 0
compared = 0

for gf in gen_files:
    gen = yaml.safe_load(Path(gf).read_text(encoding="utf-8"))
    gen_ev = gen["events"][0]
    date = gen_ev["date"]

    if date not in gt_events:
        print(f"\n[SKIP] {date} not in ground truth ({os.path.basename(gf)})")
        continue

    compared += 1
    gt_ev = gt_events[date]

    print(f"\nDATE {date}")
    print("-" * 70)

    if gen_ev["operation"] == gt_ev["operation"]:
        op_correct += 1
        print("Operation: OK")
    else:
        print("Operation: MISMATCH")
        print("  generated :", gen_ev["operation"])
        print("  truth     :", gt_ev["operation"])

    if gen_ev.get("depth_end_md") == gt_ev.get("depth_end_md"):
        depth_correct += 1
        print("Depth end: OK")
    else:
        print("Depth end: MISMATCH")
        print("  generated :", gen_ev.get("depth_end_md"))
        print("  truth     :", gt_ev.get("depth_end_md"))

    gt_ver = set(gt_ev.get("verification") or [])
    gen_ver = set(gen_ev.get("verification") or [])
    verif_total += len(gt_ver)
    verif_match += len(gt_ver & gen_ver)

    if gt_ver == gen_ver:
        print("Verification: OK")
    else:
        print("Verification: DIFF")
        print("  generated :", sorted(list(gen_ver)) if gen_ver else [])
        print("  truth     :", sorted(list(gt_ver)) if gt_ver else [])

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Compared days: {compared}")
print(f"Operation accuracy: {op_correct}/{compared}")
print(f"Depth end accuracy: {depth_correct}/{compared}")
print("Verification recall:", f"{verif_match}/{verif_total}" if verif_total else "N/A")
