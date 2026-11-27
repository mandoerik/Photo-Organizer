# photo-organizer

Python (CustomTkinter) GUI tool that organizes photos/videos into year/month folders by date taken, preserving metadata. Supports JPG/PNG/GIF/MP4/MOV/AVI, English + Swedish folder naming, duplicate handling, optional source cleanup. macOS + Windows.

**Only project with a GitHub remote:** `origin` → https://github.com/mandoerik/Photo-Organizer.git. So unlike Erik's other repos, pushing here is expected. (Lives inside the `photo-app/` wrapper dir.)

**Layout:** `organizer_core.py` holds all file/date/dedup logic and is Tk-free; `photo_organizer.py` is the CustomTkinter GUI on top. `tests/test_core.py` is a plain script (no pytest) — run it with a venv that has Pillow + pillow-heif; it needs no Tk. Both `venv/` and `.venv/` in the repo were created on the other machine (Intel Homebrew paths) and are broken on the work Mac, and its Homebrew Python lacks tkinter.

**Building the macOS app when the local Python lacks tkinter:** uv's standalone Python ships Tk, so `uv venv --python 3.11 <dir> && VIRTUAL_ENV=<dir> uv pip install -r requirements.txt && <dir>/bin/pyinstaller --noconfirm --distpath <out> --workpath <tmp> photo_organizer.spec`. v2.2 was built that way (Python 3.11, CustomTkinter 6.0, Tk 9.0, PyInstaller 6.22). Don't build into `dist/` while the app is running from there (`pgrep -fl MacOS/photo_organizer`). The onefile `.app` exits at once when its inner binary is exec'd directly; launch it with `open` to test.
