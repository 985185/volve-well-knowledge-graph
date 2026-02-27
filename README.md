# Volve Well Knowledge Graph (Well Dossier Manifests)

This repository generates per-well dossier manifests for the public Equinor Volve dataset by mapping:

well identifier -> relevant archive artifacts (paths only)

It does not redistribute Volve data files. It only produces structured indexes (Markdown and JSON) that reference file paths inside an existing Volve dataset mount (for example, Databricks Volume paths).

## What this produces

For each whitelisted Volve well, the generator writes:

- wells/<well>/manifest.md  (human-readable)
- wells/<well>/manifest.json (machine-readable)

Artifacts are grouped into lifecycle-relevant buckets such as:

- DDR (XML, PDF, HTML)
- Well construction and well technical reports
- Logs (LAS, DLIS, LIS)
- Survey and trajectory
- Seismic and models (where applicable)
- Other

The generator also applies:

- De-duplication by normalized filename within each well and bucket using a deterministic path-preference rule
- Foreign-well reference flagging for file rows (directories are ignored)

## Inputs

This project expects a prebuilt master catalog CSV generated elsewhere (for example, from a Databricks or Unity Catalog crawl).

You provide the catalog locally (do not commit it). The default expected filename is:

- out_wellkg_v3_catalog_v1.csv

Minimum required columns:

- path
- name
- type (file or dir)
- ext_norm
- top_folder
- tags
- well_final  (the well identifier used by the scripts)

If your catalog uses a different well column name, update the scripts accordingly.

## Quickstart

### Windows PowerShell

1) Place your catalog CSV in the repository root:

- out_wellkg_v3_catalog_v1.csv

2) Run:

```powershell
.\scripts\run_all.ps1
```

Outputs are written to:

- .\wells\

### Python (manual)

If you prefer to run the steps manually:

- Generate or update the whitelist (optional)
- Generate manifests per well

See the scripts in the scripts/ folder for the exact entry points.

## Repository layout

- scripts/
  Build whitelist and generate manifests.
- wells/
  Output manifests (tracked if you choose; large outputs are usually better in Releases).
- well_whitelist.csv
  Default whitelist artifact.

## Intended use

These manifests are designed to:

- Speed up well-centric discovery in a large, inconsistently organized archive
- Provide a deterministic evidence map for research and SPE-style studies
- Serve as a foundation for later graph work (RDF, Neo4j, NetworkX)

This repository focuses on deterministic indexing, not ML or LLM retrieval.

## License

MIT License. See License.

## Citation

See CITATION.cff.
