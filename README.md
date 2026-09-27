# AlkaMusic

<img src="assets/icon.png" width="96" align="right" alt="hranostaj">

Jednoduchá aplikace pro Windows: napíšeš názvy písniček oddělené středníkem (klidně s překlepy), klikneš na **Stáhnout** a aplikace je sama najde na YouTube a uloží jako MP3 (s interpretem, názvem a obalem) do složky **`Pisnicky` na ploše**. Když složka neexistuje, vytvoří ji sama při spuštění.

```
olympic davno; karel got lady karneval; queen bohemian rapsody
```

Soubory se jmenují **`<Název písně> - <Interpret>.mp3`**, např. `Dávno - Olympic.mp3`.

## Instalace
1. Stáhni `AlkaMusic-Setup-<verze>.exe` z [nejnovějšího vydání](https://github.com/Bacilek/AlkaMusic/releases/latest) (nebo ho přenes flashkou).
2. Spusť ho. Pokud se objeví *„Systém Windows ochránil váš počítač“*, klikni na *Další informace* → *Přesto spustit* (instalátor není podepsaný). Při přenosu flashkou se okno neukáže.
3. Instalace proběhne sama (bez admin práv) do `%LOCALAPPDATA%\Programs\AlkaMusic` a vytvoří zástupce **AlkaMusic** (hranostaj) na ploše a v nabídce Start.

**Aktualizace:** stáhni a spusť novější instalátor, přepíše starou verzi.
**Odinstalace:** *Nastavení → Aplikace → Nainstalované aplikace → AlkaMusic → Odinstalovat*. Smaže aplikaci, zástupce i stažené nástroje (yt-dlp, ffmpeg), historii a log. Složka `Pisnicky` s písničkami zůstane.

## Jak to funguje
1. Nejdřív se hledá na **YouTube Music** mezi písněmi (studiové verze, dobře zvládá překlepy).
2. Když tam nic nesedí, použije se běžné hledání na YouTube a [ranker](alkamusic/ranker.py) vybere nejlepší video. Přeskakuje živáky, covery, remixy, karaoke a hodinové smyčky (pokud je výslovně nechceš).
3. Stahuje se přes [yt-dlp](https://github.com/yt-dlp/yt-dlp), do MP3 převádí ffmpeg, tagy (název, interpret, album) a čtvercový obal se vloží automaticky.
4. Co už je stažené, se podruhé nestahuje („už máš“). Neúspěšné stažení se jednou tiše zopakuje, pak se u položky objeví „Zkusit znovu“.

yt-dlp a ffmpeg si aplikace stáhne sama při prvním spuštění (asi 120 MB, jen jednou) do `%LOCALAPPDATA%\AlkaMusic\bin`. yt-dlp se při každém spuštění sám aktualizuje. Když stahování přestane fungovat, obvykle stačí aplikaci restartovat.

Interní data (`%LOCALAPPDATA%\AlkaMusic`): `bin\` (yt-dlp, ffmpeg), `history.json` (stažená videa), `log.txt` (chyby).

## Tipy
- **Řazení podle data:** ve složce `Pisnicky` zvol jednou *Seřadit → Datum změny* a *Seřadit → Sestupně*. Windows si to zapamatuje. Z programu to spolehlivě nastavit nejde. Datum změny souboru = čas stažení.
- **Do telefonu:** obsah složky `Pisnicky` zkopíruj kabelem do složky `Music` v telefonu (nebo přes Quick Share). Samsung Hudba písničky zobrazí i s obaly a umí řadit podle data přidání.

## Vývoj
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m alkamusic      # spuštění
.\.venv\Scripts\python -m pytest         # testy
.\build.ps1                              # testy + dist\AlkaMusic\ + dist\AlkaMusic-Setup-<verze>.exe
                                         # (potřebuje Inno Setup: winget install JRSoftware.InnoSetup)
.\.venv\Scripts\python assets\make_icon.py   # přegeneruje ikonu hranostaje
```

---
Jen pro osobní použití. Stahování z YouTube je v rozporu s jeho podmínkami užití.
