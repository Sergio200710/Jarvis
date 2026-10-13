# Construye el ejecutable de Jarvis con PyInstaller.
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creando entorno virtual..."
    python -m venv (Join-Path $root ".venv")
}

& $python -m pip install -r (Join-Path $root "requirements-dev.txt")

Push-Location $root
try {
    & $python -m PyInstaller --noconfirm --clean "jarvis.spec"
}
finally {
    Pop-Location
}

Write-Host "Listo. Ejecutable en dist\Jarvis\Jarvis.exe"
