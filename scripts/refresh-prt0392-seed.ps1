$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

python scripts\prt0392_qa.py refresh
python scripts\prt0392_qa.py verify

Write-Host 'PRT-0392 rolling QA fixtures refreshed and verified.'
