import pandas as pd

IN_CSV = "out_wellkg_v3_catalog_v1.csv"
OUT_WHITELIST = "well_whitelist.csv"

# Folders that are most likely to contain real well-scoped assets
TRUST_FOLDERS = {"Well_logs_pr_WELL", "Well_logs", "Well_technical_data"}

# Minimum evidence threshold to be considered "real"
# Adjust if needed: 30 is a good start, fake wells usually have < 10
MIN_ROWS = 30

def main():
    df = pd.read_csv(IN_CSV, dtype=str, low_memory=False).fillna("")
    df = df[df["well_final"].str.strip() != ""].copy()

    df_trust = df[df["top_folder"].isin(TRUST_FOLDERS)].copy()

    counts = df_trust["well_final"].value_counts().reset_index()
    counts.columns = ["well_id", "trusted_rows"]

    # whitelist rule
    wl = counts[counts["trusted_rows"] >= MIN_ROWS].copy()
    wl = wl.sort_values(["trusted_rows", "well_id"], ascending=[False, True])

    wl.to_csv(OUT_WHITELIST, index=False)

    print("Wrote:", OUT_WHITELIST)
    print("\n=== Whitelisted wells ===")
    print(wl.to_string(index=False))

    print("\n=== Dropped candidates (below threshold) ===")
    dropped = counts[counts["trusted_rows"] < MIN_ROWS].copy()
    print(dropped.head(50).to_string(index=False))

if __name__ == "__main__":
    main()