# AlkaMusic

Jednoduchá aplikace pro Windows: napíšeš názvy písniček oddělené středníkem (klidně s překlepy), klikneš na **Stáhnout** a aplikace je sama najde na YouTube a uloží jako MP3 (s interpretem, názvem a obalem) do složky `Pisnicky` na ploše (vytvoří ji sama, když neexistuje).

```
olympic davno; karel got lady karneval; queen bohemian rapsody
```

## Jak to funguje
1. Nejdřív se hledá na **YouTube Music** mezi písněmi (studiové verze, dobře zvládá překlepy).
2. Když tam nic nesedí, použije se běžné hledání na YouTube a [ranker](alkamusic/ranker.py) vybere nejlepší video. Přeskakuje živáky, covery, remixy, karaoke a hodinové smyčky (pokud je výslovně nechceš).
3. Stahuje se přes [yt-dlp](https://github.com/yt-dlp/yt-dlp), do MP3 převádí ffmpeg, tagy a čtvercový obal se vloží automaticky.
4. Co už je stažené, se podruhé nestahuje.

yt-dlp a ffmpeg si aplikace stáhne sama při prvním spuštění (asi 120 MB, jen jednou) do `%LOCALAPPDATA%\AlkaMusic\bin`. yt-dlp se při každém spuštění sám aktualizuje. Když stahování přestane fungovat, obvykle stačí aplikaci restartovat.
Chyby se zapisují do `%LOCALAPPDATA%\AlkaMusic\log.txt`.

## Vývoj
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m alkamusic      # spuštění
.\.venv\Scripts\python -m pytest         # testy
.\build.ps1                              # -> dist\AlkaMusic.exe
```

## Do telefonu
Obsah složky `Pisnicky` z plochy zkopíruj kabelem do složky `Music` v telefonu (nebo přes Quick Share). Samsung Hudba písničky zobrazí i s obaly.

---
Jen pro osobní použití. Stahování z YouTube je v rozporu s jeho podmínkami užití.
