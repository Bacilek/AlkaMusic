# CLAUDE.md

## Účel
Windows appka pro uživatelovu maminku (netechnická uživatelka, Samsung telefon, bez Spotify). Vloží názvy písniček oddělené `;` (nebo po řádcích, klidně s překlepy) → appka sama najde nejlepší verzi na YouTube a uloží MP3. Priorita: **jednoduché, svižné, minimum vizuálního smogu**. Komunikace s uživatelem a veškeré UI texty **česky**.

## Pevná rozhodnutí (neměnit bez dotazu)
- **Windows desktop** (Python + CustomTkinter → PyInstaller onefile exe). Android verze zvažována a odložena.
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
- `install.py` – samoinstalace (jen frozen exe): když exe neběží z `%LOCALAPPDATA%\Programs\AlkaMusic`, zkopíruje se tam (= i aktualizace), smaže `:Zone.Identifier` (SmartScreen se už neptá), vytvoří zástupce na ploše + ve Start menu (PowerShell WScript.Shell) a spustí nainstalovanou kopii s `PYINSTALLER_RESET_ENVIRONMENT=1`. Selhání → log a běh z aktuálního místa.
- `ui.py` – jedno okno; řádky seznamu jsou obyčejné `tk.Label` (rychlé i pro stovky položek), UI polluje joby přes `after(250)`.

## Příkazy
- Testy: `.\.venv\Scripts\python -m pytest -q` (tests/test_ranker.py – ranker, naming, parse_input).
- Spuštění: `.\.venv\Scripts\python -m alkamusic`
- Build: `powershell -ExecutionPolicy Bypass -File .\build.ps1` → `dist\AlkaMusic.exe` (~20 MB; build spouští i testy).
- Ruční e2e ověření: engine lze použít bez GUI (`Engine(); start_setup(); add(Job(q))`, přepsat `out_dir`); izolovaný „čistý PC“ test = nastavit `LOCALAPPDATA` na prázdnou složku a odebrat ffmpeg z PATH.

## Vydání (uživatel chce mít aktuální build vždy na GitHubu)
Po každé změně kódu: build → commit → push `app` i `main` (main = fast-forward z `app`) → nový GitHub Release s `dist\AlkaMusic.exe`:
`gh release create vX.Y.Z dist/AlkaMusic.exe --target main --title "AlkaMusic vX.Y.Z" --notes "…"` (verze zvyšovat; exe se do gitu necommituje).
Podepisování exe: neřešeno (certifikát drahý a SmartScreen reputaci stejně nezaručí); SmartScreen se obchází přenosem flashkou / samoinstalace odstraní MOTW.

## Pracovní zvyklosti
- **Commitovat průběžně** po každém logickém kroku a **pushovat** (i pull, pokud je remote napřed); pracuje se ve větvi `app`, `main` se fast-forwarduje (remote `origin` = github.com/Bacilek/AlkaMusic).
- Pozor: Windows PowerShell 5.1 `Get-Content`/`Set-Content` bez `-Encoding utf8` **rozbije diakritiku** v UTF-8 souborech – pro hromadné úpravy textu používat Python nebo nástroje Edit/Write. Commit messages přes Bash heredoc (`git commit -F -`), ne přes PowerShell here-string.
- Po změně UI ověřit screenshotem (Pillow `ImageGrab` ve skriptu, který App spustí a vloží text).
