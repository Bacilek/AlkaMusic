"""Writes the Windows version resource for PyInstaller (--version-file).

Usage: python installer/make_version_info.py <output file>
"""

import sys
from pathlib import Path

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo, VarStruct, VSVersionInfo,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from alkamusic import __version__  # noqa: E402

numbers = tuple(int(n) for n in __version__.split(".")) + (0,)
info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=numbers, prodvers=numbers),
    kids=[
        StringFileInfo([StringTable("040504B0", [
            StringStruct("CompanyName", "Bacilek"),
            StringStruct("FileDescription", "AlkaMusic - stahování písniček"),
            StringStruct("FileVersion", __version__),
            StringStruct("InternalName", "AlkaMusic"),
            StringStruct("LegalCopyright", "Bacilek"),
            StringStruct("OriginalFilename", "AlkaMusic.exe"),
            StringStruct("ProductName", "AlkaMusic"),
            StringStruct("ProductVersion", __version__),
        ])]),
        VarFileInfo([VarStruct("Translation", [0x0405, 1200])]),
    ],
)
Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)
Path(sys.argv[1]).write_text(str(info), encoding="utf-8")
