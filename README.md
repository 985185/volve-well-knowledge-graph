# Volve Well Knowledge Graph (Dossier Manifests)

This repository generates per-well “dossier” manifests for the public Equinor Volve dataset by mapping:

**well ID → relevant archive artifacts (paths only)**

It does **not** redistribute Volve data files. It only produces structured indexes (Markdown + JSON) containing file paths within an existing Volve dataset mount (e.g., Databricks Volume paths).

Repository purpose: make well-centric discovery and evidence mapping fast and reproducible for petroleum engineering research.

## What this produces

For each whitelisted Volve well, the generator writes:

- `wells/<well>/manifest.md` — human-readable dossier
- `wells/<well>/manifest.json` — machine-readable dossier

Artifacts are bucketed into lifecycle-relevant categories such as:

- `Well_Construction_Reports`
- `DDR_HTML`, `DDR_PDF`, `DDR_XML`
- `Logs`
- `Survey_Trajectory`
- `WellTechnical_General`
- `Other`

In addition, the current generator applies:

- De-duplication by normalized filename within each well and bucket, using a path-preference rule (e.g., prefers `Well_logs_pr_WELL` over `Well_logs`)
- Foreign-well reference flagging on **files only** (directories are ignored)

## Inputs

This project expects a prebuilt master catalog CSV generated elsewhere (for example, from a Databricks/Unity Catalog crawl).

You must provide locally (do not commit):

- `out_wellkg_v3_catalog_v1.csv`

Required columns (minimum):

- `path`
- `name`
- `type` (file/dir)
- `ext_norm`
- `top_folder`
- `tags`
- `well_final`  ← this is the well identifier used by the scripts

## Quickstart (Windows PowerShell)

1) Place your catalog CSV in the repo root:

- `out_wellkg_v3_catalog_v1.csv`

2) Run:

```powershell
.\scripts\run_all.ps1
