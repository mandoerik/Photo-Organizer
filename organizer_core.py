"""
Core logic for Photo & Video Organizer.

Everything in here is independent of Tkinter so it can be unit-tested and
reused from a CLI. The GUI in photo_organizer.py is a thin layer on top.
"""

import filecmp
import logging
import logging.handlers
import os
import shutil
import struct
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional, Tuple

log = logging.getLogger("photo_organizer")

# Optional HEIC/HEIF support (iPhone default format). Registers a Pillow
# opener so Image.open() understands .heic; silently unavailable otherwise.
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIF_SUPPORTED = True
except Exception:  # pragma: no cover - depends on environment
    HEIF_SUPPORTED = False


# --- Supported formats ------------------------------------------------------

PHOTO_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif",
    ".webp", ".tif", ".tiff", ".bmp",
)
VIDEO_EXTENSIONS = (".mp4", ".mov", ".m4v", ".3gp", ".avi", ".mkv", ".webm")

# ISO base media / QuickTime containers that carry an 'mvhd' creation time.
_MP4_EXTENSIONS = (".mp4", ".mov", ".m4v", ".3gp")

# EXIF tags, in priority order. 306 (DateTime) is the *modification* time and
# is only used when no original/digitized timestamp exists.
_EXIF_DATETIME_ORIGINAL = 36867
_EXIF_DATETIME_DIGITIZED = 36868
_EXIF_DATETIME = 306
_EXIF_IFD_POINTER = 0x8769

_EXIF_DATE_FORMATS = ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d", "%Y-%m-%d")

# Seconds between the QuickTime epoch (1904-01-01) and the Unix epoch.
_MP4_EPOCH_OFFSET = 2082844800

# Timestamps earlier than this are treated as "unset" (cameras that write
# zeros end up in 1904 or 1970).
_MIN_PLAUSIBLE_YEAR = 1980


# --- Month names ------------------------------------------------------------

MONTH_NAMES = {
    "English": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
    "Swedish": [
        "Januari", "Februari", "Mars", "April", "Maj", "Juni",
        "Juli", "Augusti", "September", "Oktober", "November", "December",
    ],
}

UNKNOWN_DATE_FOLDER = {
    "English": "Unknown Date",
    "Swedish": "Okänt datum",
}


def extensions_for(selection: str) -> Tuple[str, ...]:
    """Map the UI selection ('all' | 'photos' | 'videos') to extensions."""
    if selection == "photos":
        return PHOTO_EXTENSIONS
    if selection == "videos":
        return VIDEO_EXTENSIONS
    return PHOTO_EXTENSIONS + VIDEO_EXTENSIONS


def is_video(path: str) -> bool:
    return path.lower().endswith(VIDEO_EXTENSIONS)


def is_photo(path: str) -> bool:
    return path.lower().endswith(PHOTO_EXTENSIONS)


# --- File discovery ---------------------------------------------------------

def collect_files(source: str, extensions: Tuple[str, ...]) -> List[str]:
    """Walk `source` and return matching files, sorted.

    Skips hidden files and folders (anything starting with '.'), which also
    removes the AppleDouble '._IMG_1234.jpg' sidecars that macOS writes on
    external drives and network shares.
    """
    result = []
    for dirpath, dirnames, filenames in os.walk(source):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            if name.lower().endswith(extensions):
                result.append(os.path.join(dirpath, name))
    return result


# --- Date extraction --------------------------------------------------------

def _parse_exif_date(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("ascii", "ignore")
    text = str(value).strip().strip("\x00").strip()
    if not text or text.startswith("0000"):
        return None
    for fmt in _EXIF_DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if parsed.year >= _MIN_PLAUSIBLE_YEAR:
            return parsed
        return None
    return None


def exif_datetime(path: str) -> Optional[datetime]:
    """Return the date taken from EXIF, or None if unavailable."""
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        return None

    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None
            try:
                exif_ifd = exif.get_ifd(_EXIF_IFD_POINTER)
            except Exception:
                exif_ifd = {}
            for source, tag in (
                (exif_ifd, _EXIF_DATETIME_ORIGINAL),
                (exif_ifd, _EXIF_DATETIME_DIGITIZED),
                (exif, _EXIF_DATETIME),
            ):
                parsed = _parse_exif_date(source.get(tag)) if source else None
                if parsed:
                    return parsed
    except Exception as e:
        log.debug("EXIF read failed for %s: %s", path, e)
    return None


def _iter_boxes(f, start: int, end: int):
    """Yield (type, payload_start, box_end) for ISO-BMFF boxes in [start, end)."""
    pos = start
    while pos + 8 <= end:
        f.seek(pos)
        header = f.read(8)
        if len(header) < 8:
            return
        size, box_type = struct.unpack(">I4s", header)
        header_len = 8
        if size == 1:
            large = f.read(8)
            if len(large) < 8:
                return
            size = struct.unpack(">Q", large)[0]
            header_len = 16
        elif size == 0:
            size = end - pos
        if size < header_len:
            return
        yield box_type, pos + header_len, pos + size
        pos += size


def mp4_creation_time(path: str) -> Optional[datetime]:
    """Read the creation time from the 'mvhd' box of an MP4/MOV/M4V/3GP file.

    Returns None if the box is missing or holds an implausible value. The
    stored time is UTC; the result is converted to local time.
    """
    try:
        file_size = os.path.getsize(path)
        with open(path, "rb") as f:
            for box_type, payload, box_end in _iter_boxes(f, 0, file_size):
                if box_type != b"moov":
                    continue
                for inner_type, inner_payload, _ in _iter_boxes(f, payload, box_end):
                    if inner_type != b"mvhd":
                        continue
                    f.seek(inner_payload)
                    version = f.read(1)
                    if not version:
                        return None
                    f.read(3)  # flags
                    if version[0] == 1:
                        raw = f.read(8)
                        if len(raw) < 8:
                            return None
                        seconds = struct.unpack(">Q", raw)[0]
                    else:
                        raw = f.read(4)
                        if len(raw) < 4:
                            return None
                        seconds = struct.unpack(">I", raw)[0]
                    if seconds == 0:
                        return None
                    try:
                        result = datetime.fromtimestamp(seconds - _MP4_EPOCH_OFFSET)
                    except (OverflowError, OSError, ValueError):
                        return None
                    if result.year < _MIN_PLAUSIBLE_YEAR:
                        return None
                    return result
                return None
    except Exception as e:
        log.debug("mvhd read failed for %s: %s", path, e)
    return None


def get_media_date(path: str) -> Optional[datetime]:
    """Best available "date taken" for a media file.

    Order: embedded metadata (EXIF for photos, mvhd for MP4-family video),
    then the file's modification time. Returns None only if even the mtime
    cannot be read, so the caller can file it under an "unknown" folder
    instead of silently using today's date.
    """
    lower = path.lower()
    date = None
    if lower.endswith(PHOTO_EXTENSIONS):
        date = exif_datetime(path)
    elif lower.endswith(_MP4_EXTENSIONS):
        date = mp4_creation_time(path)
    if date:
        return date
    try:
        return datetime.fromtimestamp(os.path.getmtime(path))
    except Exception as e:
        log.warning("Could not determine any date for %s: %s", path, e)
        return None


def date_folder(date: Optional[datetime], language: str) -> Tuple[str, ...]:
    """Relative folder path components for a date, e.g. ('2024', 'Mars')."""
    names = MONTH_NAMES.get(language, MONTH_NAMES["English"])
    if date is None:
        return (UNKNOWN_DATE_FOLDER.get(language, UNKNOWN_DATE_FOLDER["English"]),)
    return (str(date.year), names[date.month - 1])


# --- Destination resolution -------------------------------------------------

def files_identical(a: str, b: str) -> bool:
    """True if two files have identical content (size check first)."""
    try:
        if os.path.getsize(a) != os.path.getsize(b):
            return False
        return filecmp.cmp(a, b, shallow=False)
    except OSError:
        return False


def resolve_destination(dest_dir: str, src_path: str) -> Optional[str]:
    """Pick a free destination path for `src_path` inside `dest_dir`.

    Returns None if a byte-identical copy already exists there (under the
    original name or any of the '_N' variants), so the caller can skip it
    instead of producing IMG_1.jpg, IMG_2.jpg duplicates on repeated runs.
    """
    filename = os.path.basename(src_path)
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(dest_dir, filename)
    counter = 1
    while os.path.exists(candidate):
        if files_identical(src_path, candidate):
            return None
        candidate = os.path.join(dest_dir, f"{base}_{counter}{ext}")
        counter += 1
    return candidate


# --- Logging ----------------------------------------------------------------

def log_dir() -> str:
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Logs/Photo Organizer")
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "PhotoOrganizer", "Logs")
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    return os.path.join(base, "photo-organizer")


def log_file_path() -> str:
    return os.path.join(log_dir(), "photo_organizer.log")


def configure_logging() -> Optional[str]:
    """Attach a rotating file handler once. Returns the log path, or None."""
    if getattr(configure_logging, "_done", False):
        return getattr(configure_logging, "_path", None)
    path = None
    try:
        os.makedirs(log_dir(), exist_ok=True)
        path = log_file_path()
        handler = logging.handlers.RotatingFileHandler(
            path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        log.addHandler(handler)
        log.setLevel(logging.INFO)
    except Exception:
        path = None
    configure_logging._done = True
    configure_logging._path = path
    return path


# --- Validation -------------------------------------------------------------

def validate_paths(source: str, destinations: List[str]) -> Optional[str]:
    """Return an error message, or None if the layout is safe."""
    source = os.path.realpath(source)
    if not os.path.isdir(source):
        return "Source folder does not exist."
    for dest in destinations:
        if not dest:
            continue
        dest = os.path.realpath(dest)
        if source == dest:
            return "Source and destination cannot be the same."
        if dest.startswith(source + os.sep):
            return "Destination cannot be inside the source folder."
        if source.startswith(dest + os.sep):
            return "Source is inside the destination."
    return None


# --- The job itself ---------------------------------------------------------

@dataclass
class Job:
    source: str
    photo_dest: str
    video_dest: str
    extensions: Tuple[str, ...]
    language: str = "English"
    delete_source: bool = False


@dataclass
class Result:
    total: int = 0
    processed: int = 0
    transferred: int = 0
    skipped: int = 0
    errors: List[Tuple[str, str]] = field(default_factory=list)
    cancelled: bool = False


ProgressCallback = Callable[[int, int, str], None]


def organize(
    job: Job,
    progress: Optional[ProgressCallback] = None,
    should_cancel: Optional[Callable[[], bool]] = None,
) -> Result:
    """Run the whole organization. Safe to call from a worker thread.

    `progress(processed, total, filename)` is called after every file.
    `should_cancel()` is polled between files.
    """
    result = Result()
    action = "move" if job.delete_source else "copy"
    files = collect_files(job.source, job.extensions)
    result.total = len(files)
    log.info("Starting %s of %d files from %s", action, result.total, job.source)

    for file_path in files:
        if should_cancel and should_cancel():
            result.cancelled = True
            log.info("Cancelled after %d of %d files", result.processed, result.total)
            return result

        try:
            dest_base = job.video_dest if is_video(file_path) else job.photo_dest
            date = get_media_date(file_path)
            dest_dir = os.path.join(dest_base, *date_folder(date, job.language))
            os.makedirs(dest_dir, exist_ok=True)

            dest_path = resolve_destination(dest_dir, file_path)
            if dest_path is None:
                result.skipped += 1
                if job.delete_source:
                    os.remove(file_path)
                    log.info("Identical copy already in %s, removed source %s", dest_dir, file_path)
                else:
                    log.info("Identical copy already in %s, skipped %s", dest_dir, file_path)
            else:
                if job.delete_source:
                    shutil.move(file_path, dest_path)
                else:
                    shutil.copy2(file_path, dest_path)
                result.transferred += 1
        except Exception as e:
            message = f"{type(e).__name__}: {e}"
            result.errors.append((file_path, message))
            log.error("Failed to %s %s: %s", action, file_path, message)

        result.processed += 1
        if progress:
            progress(result.processed, result.total, os.path.basename(file_path))

    log.info(
        "Done: %d %s, %d skipped, %d failed",
        result.transferred, "moved" if job.delete_source else "copied",
        result.skipped, len(result.errors),
    )
    return result
