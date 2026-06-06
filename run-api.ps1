# Tiny launcher for the FinOps API + dashboard.
# Run with:  powershell -ExecutionPolicy Bypass -File run-api.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "services/api-service")

Write-Host "---------------------------------------------------------------"
Write-Host " FinOps API + dashboard"
Write-Host " Dashboard : http://127.0.0.1:8000"
Write-Host " API docs  : http://127.0.0.1:8000/docs"
Write-Host " (Press Ctrl+C to stop the server.)"
Write-Host "---------------------------------------------------------------"

Start-Process "http://127.0.0.1:8000"
api-service --db-path ../ingestion-service/data/finops.db
