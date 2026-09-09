# Build a standalone InstaMusicDownloader.exe with ffmpeg bundled inside.
# Run from the project root: .\scripts\build.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$FfmpegExe = Join-Path $ProjectRoot "vendor\ffmpeg\ffmpeg.exe"
if (-not (Test-Path $FfmpegExe)) {
    Write-Host "ffmpeg.exe not found, fetching it first..."
    python scripts\fetch_ffmpeg.py
}

$IconIco = Join-Path $ProjectRoot "app\assets\icon.ico"
$SplashPng = Join-Path $ProjectRoot "app\assets\splash.png"
if (-not (Test-Path $IconIco) -or -not (Test-Path $SplashPng)) {
    Write-Host "icon/splash assets not found, generating them first..."
    python scripts\generate_assets.py
}

pyinstaller --name InstaMusicDownloader `
    --onefile `
    --noconsole `
    --icon "$IconIco" `
    --splash "$SplashPng" `
    --add-binary "$FfmpegExe;ffmpeg" `
    --add-data "$IconIco;icon" `
    app\main.py

Write-Host "Build complete: dist\InstaMusicDownloader.exe"
