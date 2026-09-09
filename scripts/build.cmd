@echo off
rem Wrapper for build.ps1 that bypasses the PowerShell script execution policy
rem for this process only, without changing any system-wide security settings.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" %*
