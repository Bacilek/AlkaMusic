"""Self-install of the built exe: the downloaded AlkaMusic.exe copies itself to
%LOCALAPPDATA%\\Programs\\AlkaMusic, creates desktop + Start menu shortcuts and restarts
from there. Running a newer downloaded exe again works as an update. No admin rights needed.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .engine import NO_WINDOW, desktop_dir, log

APP_NAME = "AlkaMusic"
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Programs" / APP_NAME
INSTALLED_EXE = INSTALL_DIR / f"{APP_NAME}.exe"
START_MENU = Path(os.environ.get("APPDATA", Path.home())) / "Microsoft/Windows/Start Menu/Programs"


def _ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def _create_shortcut(lnk, target):
    script = (
        f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut({_ps_quote(lnk)});"
        f"$s.TargetPath = {_ps_quote(target)};"
        f"$s.WorkingDirectory = {_ps_quote(target.parent)};"
        f"$s.IconLocation = {_ps_quote(f'{target},0')};"
        "$s.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        creationflags=NO_WINDOW, timeout=30, check=True,
    )


def _unblock(path):
    """Removes the 'downloaded from the internet' mark, so Windows SmartScreen won't ask again."""
    try:
        os.remove(f"{path}:Zone.Identifier")
    except OSError:
        pass


def ensure_installed():
    """Returns True when the installed copy was started and this process should exit."""
    if not getattr(sys, "frozen", False):
        return False  # running from source
    current = Path(sys.executable).resolve()
    if current == INSTALLED_EXE.resolve():
        return False
    try:
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(current, INSTALLED_EXE)
        _unblock(INSTALLED_EXE)
        for folder in (desktop_dir(), START_MENU):
            _create_shortcut(folder / f"{APP_NAME}.lnk", INSTALLED_EXE)
        env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1")
        subprocess.Popen([str(INSTALLED_EXE)], cwd=INSTALL_DIR, env=env)
        return True
    except Exception:
        log.exception("Install failed, running from %s", current)
        return False  # e.g. the installed copy is running right now - just run from here
