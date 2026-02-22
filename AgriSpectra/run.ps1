<#
run.ps1
Bootstrap and run the AgriSpectra Flask app on Windows.

Behavior:
- Uses system `python` or `py` if available.
- If Python is missing and `winget` is available, attempts a silent install of Python 3.
- Creates a `.venv`, installs `requirements.txt`, and starts `app.py` using the venv Python.

Run from PowerShell in the project folder:
    .\run.ps1
#>

param()

Set-StrictMode -Version Latest

$project = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $project

function Has-Command($name){
    return (Get-Command $name -ErrorAction SilentlyContinue) -ne $null
}

$pyExe = $null
$pyArgs = $null

if (Has-Command python) {
    $pyExe = (Get-Command python).Source
} elseif (Has-Command py) {
    $pyExe = (Get-Command py).Source
    $pyArgs = '-3'
} else {
    Write-Host "Python not found."
    if (Has-Command winget) {
        Write-Host "Attempting to install Python via winget..."
        & winget install --id Python.Python.3 -e --silent
        Start-Sleep -Seconds 3
        if (Has-Command python) {
            $pyExe = (Get-Command python).Source
        } elseif (Has-Command py) {
            $pyExe = (Get-Command py).Source
            $pyArgs = '-3'
        } else {
            Write-Error "Python installation via winget did not make 'python' available. Please install Python manually and re-run."
            exit 1
        }
    } else {
        Write-Error "No python or winget found. Please install Python 3.8+ and re-run."
        exit 1
    }
}

Write-Host "Using Python executable: $pyExe $pyArgs"

# create virtualenv
if ($pyArgs) {
    & $pyExe $pyArgs -m venv .venv
} else {
    & $pyExe -m venv .venv
}

$venvPython = Join-Path $project ".venv\Scripts\python.exe"

if (-Not (Test-Path $venvPython)) {
    Write-Error "Virtual environment creation failed or $venvPython not found."
    exit 1
}

# upgrade pip and install requirements
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

# run the flask app
Write-Host "Starting the Flask app..."
& $venvPython app.py
