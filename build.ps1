# Builds dist\AlkaMusic.exe (single file, no console window).
# yt-dlp and ffmpeg are not bundled - the app downloads them on first start.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python -m pip install -q -r requirements.txt
.\.venv\Scripts\python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }

.\.venv\Scripts\pyinstaller --noconfirm --clean --onefile --windowed `
    --name AlkaMusic --icon assets\icon.ico `
    --add-data "assets\icon.ico;assets" --add-data "assets\icon.png;assets" `
    --collect-data customtkinter --paths . `
    alkamusic\__main__.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

Write-Host "Hotovo: dist\AlkaMusic.exe"
