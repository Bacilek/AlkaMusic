"""Parses YouTube titles (usually 'Artist - Title') and builds '<Song> - <Artist>' file names."""

import re

_JUNK = (
    r"official|video|audio|lyric|lyrics|text|hd|hq|4k|remaster|remastered|videoclip|klip"
    r"|clip|visuali[sz]er|m/v|mv|music|oficial|oficialni|oficiální|videoklip"
)
_BRACKETS = re.compile(r"\s*[\(\[\{]([^\)\]\}]*)[\)\]\}]")
_SEPARATORS = re.compile(r"\s+[-–—]\s+")
_BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def clean_title(title):
    def repl(m):
        inner = m.group(1).lower()
        return "" if re.search(rf"\b({_JUNK})\b", inner) or re.fullmatch(r"\s*\d{4}\s*", inner) else m.group(0)

    title = _BRACKETS.sub(repl, title)
    title = title.split(" | ")[0]
    return re.sub(r"\s{2,}", " ", title).strip(" -–—")


def artist_title(title, channel):
    clean = clean_title(title or "")
    parts = _SEPARATORS.split(clean, maxsplit=1)
    if len(parts) == 2 and parts[0] and parts[1]:
        return parts[0].strip(), parts[1].strip()
    artist = re.sub(r"(\s+-\s+Topic|VEVO|\s+Official)$", "", channel or "", flags=re.I).strip()
    return artist, clean


def display_name(artist, title):
    """Name used for the file and in the UI: '<Song> - <Artist>'."""
    return f"{title} - {artist}" if artist else title


def safe_filename(name):
    name = _BAD_CHARS.sub("", name).strip(" .")
    return name[:150] or "pisnicka"
