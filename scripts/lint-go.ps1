# Run golangci-lint on all Go modules locally.
# Usage: .\scripts\lint-go.ps1
# Prerequisites: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

$ErrorActionPreference = "Continue"

$GO_MODULES = @("services/api-gateway", "services/backend", "services/operator", "shared/types")

$failed = $false

foreach ($d in $GO_MODULES) {
    if (-not (Test-Path $d)) {
        continue
    }
    Write-Host "--- Linting $d ---" -ForegroundColor Cyan
    Push-Location $d
    golangci-lint run ./...
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAIL: $d" -ForegroundColor Red
        $failed = $true
    } else {
        Write-Host "PASS: $d" -ForegroundColor Green
    }
    Pop-Location
    Write-Host ""
}

if ($failed) {
    Write-Host "Lint failed." -ForegroundColor Red
    exit 1
}

Write-Host "All modules passed." -ForegroundColor Green
