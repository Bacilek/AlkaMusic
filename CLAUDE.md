# CLAUDE.md

## Účel
Windows appka pro uživatelovu maminku (netechnická uživatelka, Samsung telefon, bez Spotify). Vloží názvy písniček oddělené `;` (nebo po řádcích, klidně s překlepy) → appka sama najde nejlepší verzi na YouTube a uloží MP3. Priorita: **jednoduché, svižné, minimum vizuálního smogu**. Komunikace s uživatelem a veškeré UI texty **česky**.

## Pevná rozhodnutí (neměnit bez dotazu)
- **Windows desktop** (Python + CustomTkinter → PyInstaller **onedir** → **Inno Setup instalátor** `AlkaMusic-Setup-<verze>.exe`). Uživatel chtěl instalační balíček místo holého exe (působí bezpečněji; onefile navíc spouštěl hlášku „This app can't run on your PC“). Android verze zvažována a odložena.
- **Plně automatický režim**, žádné vybírání z výsledků.
- Výstup: **`Plocha\Pisnicky`** (`engine.songs_dir()`, přes `FOLDERID_Desktop`, OneDrive-safe), vytvoří se při startu `Engine`.
- Název souboru i zobrazení v UI: **`<Název písně> - <Interpret>`** (`naming.display_name`).
- Ikona/avatar: roztomilý hranostaj, kreslený kódem v `assets/make_icon.py` → `icon.ico` + `icon.png`.
- yt-dlp i ffmpeg se **nebalí do exe**, stahují se při 1. spuštění do `%LOCALAPPDATA%\AlkaMusic\bin` (ffmpeg: gyan.dev essentials). `yt-dlp -U` při každém startu. Pokud je ffmpeg+ffprobe v PATH, použije se ten.
- Řazení složky podle data nejde z programu spolehlivě nastavit (ShellBags) – řeší se ručně jednou, viz README.

## Architektura (`alkamusic/`)
- `engine.py` – setup (stažení/aktualizace nástrojů), `parse_input`, hledání, stahování, fronta (2 worker vlákna, 1 tichý retry), `Job` stavy, log do `%LOCALAPPDATA%\AlkaMusic\log.txt`.
  - Hledání: nejdřív **YouTube Music songs** (`music.youtube.com/search?q=…#songs`, flat) → `ranker.best_song` (slova titulu musí být v dotazu, max. top 3). Fallback `ytsearch6:` → `ranker.best`.
  - Stahování: `-x mp3 --audio-quality 0`, embed thumbnail oříznutý na čtverec (`SQUARE_COVER` ppa), `--print before_dl:` s markerem `META` vrací artist/track/album z YouTube → mají přednost před jménem odhadnutým z titulu. Tagy dopisuje `mutagen`.
- `ranker.py` – skórování (Topic kanál bonus, penalizace live/cover/remix/karaoke/…, pokud nejsou v dotazu; délka <1 min / >10 min).
- `naming.py` – čištění titulů („(Official Video)“, „[HD]“, rok…), `artist_title`, `safe_filename`.
- `history.py` – JSON video_id → cesta; duplicity se přeskočí („už máš“), pokud soubor stále existuje.
- `__init__.py` – `__version__` (jediný zdroj verze; build z ní generuje version resource exe i název instalátoru).
- `ui.py` – jedno okno; řádky seznamu jsou obyčejné `tk.Label` (rychlé i pro stovky položek), UI polluje joby přes `after(250)`.

## Příkazy
- Testy: `.\.venv\Scripts\python -m pytest -q` (tests/test_ranker.py – ranker, naming, parse_input).
- Spuštění: `.\.venv\Scripts\python -m alkamusic`
- Build: `powershell -ExecutionPolicy Bypass -File .\build.ps1` → testy, `dist\AlkaMusic\` (onedir, exe s version info přes `installer/make_version_info.py`) a `dist\AlkaMusic-Setup-<verze>.exe` (~15 MB, `installer/AlkaMusic.iss`, Inno Setup v `%LOCALAPPDATA%\Programs\Inno Setup 6`, instalace `winget install JRSoftware.InnoSetup`).
- Instalátor: per-user (bez admina) do `%LOCALAPPDATA%\Programs\AlkaMusic`, zástupci plocha + Start, záznam v Aplikace. Odinstalace nejdřív `taskkill /T` běžící appky, pak smaže `{app}` i `%LOCALAPPDATA%\AlkaMusic` (yt-dlp, ffmpeg, historie, log); `Plocha\Pisnicky` nechává.
- Test instalátoru: `Setup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART`, odinstalace `unins000.exe` se stejnými přepínači.
- Ruční e2e ověření: engine lze použít bez GUI (`Engine(); start_setup(); add(Job(q))`, přepsat `out_dir`); izolovaný „čistý PC“ test = nastavit `LOCALAPPDATA` na prázdnou složku a odebrat ffmpeg z PATH.

## Vydání (uživatel chce mít aktuální build vždy na GitHubu)
Po každé změně kódu: zvýšit `__version__` → build → commit → push `app` i `main` (main = fast-forward z `app`) → nový GitHub Release s instalátorem:
`gh release create vX.Y.Z dist/AlkaMusic-Setup-X.Y.Z.exe --target main --title "AlkaMusic vX.Y.Z" --notes "…"` (build artefakty se do gitu necommitují).
Podepisování exe: neřešeno (certifikát drahý a SmartScreen reputaci stejně nezaručí); SmartScreen se u staženého instalátoru ukáže jednou (Další informace → Přesto spustit), při přenosu flashkou vůbec.

## Pracovní zvyklosti
- **Commitovat průběžně** po každém logickém kroku a **pushovat** (i pull, pokud je remote napřed); pracuje se ve větvi `app`, `main` se fast-forwarduje (remote `origin` = github.com/Bacilek/AlkaMusic).
- Pozor: Windows PowerShell 5.1 `Get-Content`/`Set-Content` bez `-Encoding utf8` **rozbije diakritiku** v UTF-8 souborech – pro hromadné úpravy textu používat Python nebo nástroje Edit/Write. Commit messages přes Bash heredoc (`git commit -F -`), ne přes PowerShell here-string.
- Po změně UI ověřit screenshotem (Pillow `ImageGrab` ve skriptu, který App spustí a vloží text).
