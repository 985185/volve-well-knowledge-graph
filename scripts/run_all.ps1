# run_all.ps1
# End-to-end run for dossier generation (expects out_wellkg_v3_catalog_v1.csv present)

$ErrorActionPreference = "Stop"

Write-Host "Running Volve Well Dossiers pipeline..."

if (!(Test-Path ".\out_wellkg_v3_catalog_v1.csv")) {
  throw "Missing out_wellkg_v3_catalog_v1.csv in current folder."
}

python .\scripts\build_well_whitelist.py
python .\scripts\generate_manifests_v1_3.py

Write-Host ""
Write-Host "Done. Output in .\wells"