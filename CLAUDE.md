# photo-organizer

Python (CustomTkinter) GUI tool that organizes photos/videos into year/month folders by date taken, preserving metadata. Supports JPG/PNG/GIF/MP4/MOV/AVI, English + Swedish folder naming, duplicate handling, optional source cleanup. macOS + Windows.

**Only project with a GitHub remote:** `origin` → https://github.com/mandoerik/Photo-Organizer.git. So unlike Erik's other repos, pushing here is expected. (Lives inside the `photo-app/` wrapper dir.)

**Layout:** `organizer_core.py` holds all file/date/dedup logic and is Tk-free; `photo_organizer.py` is the CustomTkinter GUI on top. `tests/test_core.py` is a plain script (no pytest) — run it with a venv that has Pillow + pillow-heif; it needs no Tk. Both `venv/` and `.venv/` in the repo were created on the other machine (Intel Homebrew paths) and are broken on the work Mac; the Homebrew Python there lacks tkinter, so the GUI cannot be launched on it — only the core tests.
