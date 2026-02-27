#!/usr/bin/env bash
set -euo pipefail

echo "Running Volve Well Dossiers pipeline..."

if [[ ! -f "./out_wellkg_v3_catalog_v1.csv" ]]; then
  echo "ERROR: Missing out_wellkg_v3_catalog_v1.csv in current folder." >&2
  exit 1
fi

python3 ./scripts/build_well_whitelist.py
python3 ./scripts/generate_manifests_v1_3.py

echo ""
echo "Done. Output in ./wells"
