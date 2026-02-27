# Volve Well Knowledge Graph (Well Dossier Manifests)

This repository generates per-well dossier manifests for the public Equinor Volve dataset by mapping:

well identifier -> relevant archive artifacts (paths only)

It does not redistribute Volve data files. It only produces structured indexes (Markdown and JSON) that reference file paths inside an existing Volve dataset mount (for example, Databricks Volume paths).

## What this produces

For each whitelisted Volve well, the generator writes:

- wells/<well>/manifest.md (human-readable)
- wells/<well>/manifest.json (machine-readable)

Manifests are bucketed into lifecycle-relevant categories such as:

- Well_Construction_Reports
- DDR_XML, DDR_PDF, DDR_HTML
- Logs (LAS, DLIS, LIS plus well log folders)
- Survey_Trajectory
- WellTechnical_General
- Other

In addition, v1.3 applies:

- De-duplication by normalized filename within each well and bucket using a deterministic path-preference rule
- Cross-well reference flagging on file entries (directories are ignored)

## Generating the input catalog

This repo expects a prebuilt master catalog CSV named:

- out_wellkg_v3_catalog_v1.csv

You generate this catalog outside this repository (for example, using Databricks to crawl the Volve mount and export a CSV).

Reference pipeline:
- Volve Metadata Discovery Index (Databricks catalog crawl + tagging): https://github.com/985185/volve-metadata-index

The output of that crawl can be filtered/renamed into out_wellkg_v3_catalog_v1.csv as long as it contains the required columns listed below.

## Inputs

Minimum required columns in out_wellkg_v3_catalog_v1.csv:

- path
- name
- type (file or dir)
- ext_norm
- top_folder
- tags
- well_final (the well identifier used by the scripts)

Note: Some older documentation refers to a column named well. The current scripts use well_final.

## Quickstart

### Windows PowerShell

1) Place out_wellkg_v3_catalog_v1.csv in the repository root.
2) Run:

```powershell
.\scripts\run_all.ps1
```

### Linux / macOS (bash)

1) Place out_wellkg_v3_catalog_v1.csv in the repository root.
2) Run:

```bash
bash scripts/run_all.sh
```

If you want to make it executable:

```bash
chmod +x scripts/run_all.sh
./scripts/run_all.sh
```

Outputs are written to:

- wells/

## Repository structure

| Path | What it is |
| --- | --- |
| scripts/ | Pipeline scripts (build whitelist, generate manifests, entry points). |
| wells/ | Output manifests (per-well). Usually better to ship large outputs via GitHub Releases. |
| well_whitelist.csv | Default whitelist artifact used by the generator. |
| out_wellkg_v3_catalog_v1.csv | Input catalog (local only; do not commit). |

## De-duplication and cross-well flagging

De-duplication:
Within each well and bucket, items are de-duplicated by normalized filename. When duplicates exist, the generator keeps a single “best” path using a deterministic preference score (for example, preferring Well_logs_pr_WELL over Well_logs).

Cross-well flagging:
For file rows only, the generator scans the filename and path text for other well IDs (strict pattern match). If any are found, they are not excluded. They are included and annotated:
- manifest.json: foreign_ref_wells: ["15/9-F-..."]
- manifest.md: appended as (foreign-ref: ...)

Directories are not cross-well flagged.

## Intended use

These manifests are designed to:

- Speed up well-centric discovery in a large, inconsistently organized archive
- Provide a deterministic evidence map for research and SPE-style studies
- Serve as a foundation for later graph work (RDF, Neo4j, NetworkX)

This repository focuses on deterministic indexing, not ML or LLM retrieval.

## Requirements

See requirements.txt.

## License

MIT License. See License.

## Citation

See CITATION.cff.
