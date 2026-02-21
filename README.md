# Volve Well Dossiers

This repository generates **per-well “dossier” manifests** for the public Equinor Volve dataset by mapping **well IDs → relevant archive artifacts** (paths only).

It does **not** redistribute Volve data files. It only produces **indexes/manifests** containing file paths within an existing Volve dataset mount (e.g., Databricks Volume paths).

## What this produces

For each whitelisted Volve well, the generator writes:

- `wells/<well>/manifest.md` — human-readable dossier
- `wells/<well>/manifest.json` — machine-readable dossier

Manifests are bucketed into lifecycle-relevant categories such as:

- `Well_Construction_Reports` (drilling programme, recommendation to drill, completion reports/logs)
- `DDR_HTML`, `DDR_PDF`, `DDR_XML` (daily drilling reporting split)
- `Logs` (LAS/DLIS/LIS plus well log folders)
- `Survey_Trajectory`
- `WellTechnical_General`
- `Other`

In addition, v1.3 applies:

- **De-duplication** by normalized filename within each well and bucket (prefers `Well_logs_pr_WELL` over `Well_logs`)
- **Foreign-well reference flagging** on file entries (e.g., a PDF that mentions another well ID)

## Inputs

This project expects a prebuilt master catalog CSV (generated elsewhere) with columns:

- `path`, `name`, `type`, `ext_norm`, `well`, `top_folder`, `tags`

You should provide (locally, not committed):

- `out_wellkg_v3_catalog_v1.csv`

This repo does not regenerate the full Volve filesystem catalog from scratch.
## Intended Use

These manifests are designed to:

- Support drilling engineering research
- Enable well-centric document discovery
- Serve as a foundation for knowledge graph construction
- Provide structured evidence mapping for SPE-style studies
## Repro steps (Windows PowerShell)

Place `out_wellkg_v3_catalog_v1.csv` in the repo root, then run:

```powershell
.\scripts\run_all.ps1

