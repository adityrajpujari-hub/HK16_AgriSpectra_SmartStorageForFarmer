# Run helper for AgriSpectra
# Usage: Open PowerShell as Administrator and run: .\run_project.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$project = Join-Path $root 'AgriSpectra'
$venv = Join-Path $root 'venv'
$pythonExe = Join-Path $venv 'Scripts\python.exe'

Write-Host "Workspace root: $root"

function Check-Python {
    try {
        $pv = & python --version 2>$null
        Write-Host "Found python: $pv"
        return $true
    } catch {
        return $false
    }
}

if (-not (Check-Python)) {
    Write-Host "Python not found on PATH. Attempting to install via winget..."
    try {
        winget install --id Python.Python.3 -e --accept-package-agreements --accept-source-agreements
    } catch {
        Write-Host "winget install failed or winget not available. Please install Python 3.10+ from https://www.python.org/downloads/ and re-run this script." -ForegroundColor Yellow
        exit 1
    }
}

# Create venv if missing
if (-not (Test-Path $pythonExe)) {
    Write-Host "Creating virtual environment at $venv..."
    & python -m venv $venv
}

if (-not (Test-Path $pythonExe)) {
    Write-Host "Could not find python executable inside venv. Aborting." -ForegroundColor Red
    exit 1
}

# Upgrade pip and install requirements
Write-Host "Upgrading pip and installing requirements..."
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r (Join-Path $project 'requirements.txt')

# Run the Flask app
Write-Host "Starting AgriSpectra Flask app... (Press Ctrl+C to stop)"
& $pythonExe (Join-Path $project 'app.py')
