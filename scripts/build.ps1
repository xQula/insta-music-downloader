# Build a standalone InstaMusicDownloader.exe with ffmpeg bundled inside.
# Run from the project root: .\scripts\build.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Build from a dedicated venv (not the system/global Python) so PyInstaller
# only ever sees this project's dependencies. Building against a global
# interpreter that also has unrelated packages installed (ML libraries,
# other projects' tooling, etc.) makes PyInstaller's static import analysis
# sweep them into the exe too, bloating it by hundreds of MB for nothing.
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating build venv at .venv ..."
    python -m venv $VenvDir
}
& $VenvPython -m pip install -q --upgrade pip
& $VenvPython -m pip install -q -r requirements.txt

$FfmpegExe = Join-Path $ProjectRoot "vendor\ffmpeg\ffmpeg.exe"
if (-not (Test-Path $FfmpegExe)) {
    Write-Host "ffmpeg.exe not found, fetching it first..."
    & $VenvPython scripts\fetch_ffmpeg.py
}

$IconSvg = Join-Path $ProjectRoot "app\assets\icon.svg"
$IconIco = Join-Path $ProjectRoot "app\assets\icon.ico"
$SplashBg = Join-Path $ProjectRoot "app\assets\splash_bg.png"
if (-not (Test-Path $IconIco) -or -not (Test-Path $SplashBg)) {
    Write-Host "icon/splash assets not found, generating them first..."
    & $VenvPython scripts\generate_assets.py
}

$VenvPyInstaller = Join-Path $VenvDir "Scripts\pyinstaller.exe"
& $VenvPyInstaller --name InstaMusicDownloader `
    --onedir `
    --noconsole `
    --icon "$IconIco" `
    --add-binary "$FfmpegExe;ffmpeg" `
    --add-data "$IconIco;icon" `
    --add-data "$IconSvg;icon" `
    --add-data "$SplashBg;icon" `
    app\main.py

Write-Host "Build complete: dist\InstaMusicDownloader\InstaMusicDownloader.exe"
