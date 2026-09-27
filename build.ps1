# Builds the app folder dist\AlkaMusic\ (PyInstaller onedir) and the installer
# dist\AlkaMusic-Setup-<version>.exe (Inno Setup: winget install JRSoftware.InnoSetup).
# yt-dlp and ffmpeg are not bundled - the app downloads them on first start.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python -m pip install -q -r requirements.txt
.\.venv\Scripts\python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }

$version = (.\.venv\Scripts\python -c "import alkamusic; print(alkamusic.__version__)").Trim()
.\.venv\Scripts\python installer\make_version_info.py build\version_info.txt

.\.venv\Scripts\pyinstaller --noconfirm --clean --onedir --windowed `
    --name AlkaMusic --icon assets\icon.ico --version-file build\version_info.txt `
    --add-data "assets\icon.ico;assets" --add-data "assets\icon.png;assets" `
    --collect-data customtkinter --paths . `
    alkamusic\__main__.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup not found - winget install JRSoftware.InnoSetup" }
& $iscc /Qp "/DAppVersion=$version" installer\AlkaMusic.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }

Write-Host "Hotovo: dist\AlkaMusic-Setup-$version.exe"
