"""Tests for organizer_core. Plain script, no pytest needed: python tests/test_core.py"""
import os
import struct
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import organizer_core as core  # noqa: E402
from PIL import Image  # noqa: E402

fails = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))
    if not cond:
        fails.append(name)


def make_jpeg(path, original=None, digitized=None, modified=None, fmt="JPEG"):
    img = Image.new("RGB", (4, 4), (120, 30, 200))
    exif = Image.Exif()
    if modified:
        exif[306] = modified
    ifd = {}
    if original:
        ifd[36867] = original
    if digitized:
        ifd[36868] = digitized
    if ifd:
        exif_ifd = exif.get_ifd(0x8769)
        for k, v in ifd.items():
            exif_ifd[k] = v
    if modified or ifd:
        img.save(path, fmt, exif=exif.tobytes())
    else:
        img.save(path, fmt)


def box(typ, payload):
    return struct.pack(">I4s", 8 + len(payload), typ) + payload


def make_mp4(path, creation_secs_1904, version=0, moov_last=True):
    if version == 1:
        mvhd = bytes([1, 0, 0, 0]) + struct.pack(">QQ", creation_secs_1904, creation_secs_1904) + b"\x00" * 24
    else:
        mvhd = bytes([0, 0, 0, 0]) + struct.pack(">II", creation_secs_1904, creation_secs_1904) + b"\x00" * 16
    moov = box(b"moov", box(b"mvhd", mvhd))
    ftyp = box(b"ftyp", b"isom\x00\x00\x02\x00isomiso2mp41")
    mdat = box(b"mdat", b"\x00" * 100)
    data = ftyp + (mdat + moov if moov_last else moov + mdat)
    with open(path, "wb") as f:
        f.write(data)


def set_mtime(path, dt):
    ts = dt.timestamp()
    os.utime(path, (ts, ts))


tmp = tempfile.mkdtemp(prefix="po_test_")
src = os.path.join(tmp, "src")
dst = os.path.join(tmp, "dst")
os.makedirs(src)
os.makedirs(dst)

# 1. EXIF priority: DateTimeOriginal beats DateTime(306)
p = os.path.join(src, "edited.jpg")
make_jpeg(p, original="2019:07:04 12:00:00", modified="2024:01:15 09:00:00")
d = core.exif_datetime(p)
check("exif prefers DateTimeOriginal over DateTime", d == datetime(2019, 7, 4, 12, 0, 0), str(d))

# 2. DateTimeDigitized used when original missing
p = os.path.join(src, "digitized.jpg")
make_jpeg(p, digitized="2018:03:03 03:03:03", modified="2024:01:15 09:00:00")
check("exif falls back to DateTimeDigitized", core.exif_datetime(p) == datetime(2018, 3, 3, 3, 3, 3))

# 3. 306 used when nothing else
p = os.path.join(src, "only306.jpg")
make_jpeg(p, modified="2017:05:05 05:05:05")
check("exif uses DateTime(306) as last resort", core.exif_datetime(p) == datetime(2017, 5, 5, 5, 5, 5))

# 4. Bogus EXIF date -> mtime, not now()
p = os.path.join(src, "bogus.jpg")
make_jpeg(p, original="0000:00:00 00:00:00")
set_mtime(p, datetime(2015, 11, 20, 10, 0, 0))
d = core.get_media_date(p)
check("bogus EXIF falls back to mtime", d and d.year == 2015 and d.month == 11, str(d))

# 5. No EXIF at all -> mtime
p = os.path.join(src, "noexif.png")
make_jpeg(p, fmt="PNG")
set_mtime(p, datetime(2012, 2, 2, 2, 0, 0))
d = core.get_media_date(p)
check("no EXIF falls back to mtime", d and (d.year, d.month) == (2012, 2), str(d))

# 6. Corrupt image -> mtime, not now()
p = os.path.join(src, "corrupt.jpg")
with open(p, "wb") as f:
    f.write(b"not a jpeg at all")
set_mtime(p, datetime(2010, 6, 6))
d = core.get_media_date(p)
check("corrupt image falls back to mtime", d and (d.year, d.month) == (2010, 6), str(d))

# 7. mvhd creation time (moov after mdat, v0)
target = datetime(2021, 8, 14, 15, 30, 0)
secs = int(target.timestamp()) + core._MP4_EPOCH_OFFSET
p = os.path.join(src, "clip.mp4")
make_mp4(p, secs, version=0, moov_last=True)
set_mtime(p, datetime(2026, 9, 1))
d = core.get_media_date(p)
check("mp4 uses mvhd creation time (v0, moov last)", d == target, str(d))

# 8. mvhd v1 (64-bit)
p = os.path.join(src, "clip64.mov")
make_mp4(p, secs, version=1, moov_last=False)
set_mtime(p, datetime(2026, 9, 1))
check("mov uses mvhd creation time (v1)", core.get_media_date(p) == target)

# 9. mvhd zero -> mtime
p = os.path.join(src, "unset.m4v")
make_mp4(p, 0)
set_mtime(p, datetime(2013, 4, 4))
d = core.get_media_date(p)
check("mvhd=0 falls back to mtime", d and (d.year, d.month) == (2013, 4), str(d))

# 10. AVI (no mvhd) -> mtime
p = os.path.join(src, "old.avi")
with open(p, "wb") as f:
    f.write(b"RIFF" + b"\x00" * 64)
set_mtime(p, datetime(2009, 9, 9))
d = core.get_media_date(p)
check("avi falls back to mtime", d and d.year == 2009)

# 11. Dotfiles / AppleDouble skipped, nested dirs walked, hidden dirs skipped
os.makedirs(os.path.join(src, "sub"))
os.makedirs(os.path.join(src, ".hidden"))
make_jpeg(os.path.join(src, "sub", "nested.jpg"), original="2020:12:25 08:00:00")
with open(os.path.join(src, "._edited.jpg"), "wb") as f:
    f.write(b"\x00\x05\x16\x07")
make_jpeg(os.path.join(src, ".hidden", "secret.jpg"))
files = core.collect_files(src, core.extensions_for("all"))
names = [os.path.relpath(f, src) for f in files]
check("AppleDouble sidecar skipped", "._edited.jpg" not in names, str(names))
check("hidden dir skipped", not any(n.startswith(".hidden") for n in names))
check("nested file found", "sub/nested.jpg" in names)
check("collect count", len(names) == 11, str(len(names)))

# 12. HEIC extension recognised
check("heic in photo extensions", ".heic" in core.PHOTO_EXTENSIONS)
check("heif support loaded", core.HEIF_SUPPORTED)

# 13. Month names independent of locale
check("swedish month", core.date_folder(datetime(2024, 3, 1), "Swedish") == ("2024", "Mars"))
check("english month", core.date_folder(datetime(2024, 3, 1), "English") == ("2024", "March"))
check("unknown date folder", core.date_folder(None, "Swedish") == ("Okänt datum",))

# 14. Full organize, copy mode
job = core.Job(source=src, photo_dest=dst, video_dest=dst, extensions=core.extensions_for("all"), language="English")
progress_calls = []
res = core.organize(job, progress=lambda a, b, c: progress_calls.append((a, b, c)))
check("copy: all processed", res.processed == 11 and res.total == 11, f"{res}")
check("copy: no errors", res.errors == [], str(res.errors))
check("copy: progress called per file", len(progress_calls) == 11)
check("copy: edited.jpg in 2019/July", os.path.exists(os.path.join(dst, "2019", "July", "edited.jpg")))
check("copy: clip.mp4 in 2021/August", os.path.exists(os.path.join(dst, "2021", "August", "clip.mp4")))
check("copy: bogus.jpg in 2015/November", os.path.exists(os.path.join(dst, "2015", "November", "bogus.jpg")))
check("copy: nothing in current month", not os.path.exists(os.path.join(dst, str(datetime.now().year), datetime.now().strftime("%B"))) or datetime.now().year in (2019, 2021, 2015, 2012, 2010, 2013, 2009, 2017, 2018, 2020))
check("copy: source intact", os.path.exists(os.path.join(src, "edited.jpg")))

# 15. Second run in copy mode -> everything skipped, no _1 duplicates
res2 = core.organize(job)
check("rerun: all skipped", res2.skipped == 11 and res2.transferred == 0, f"{res2}")
dups = [f for _, _, fs in os.walk(dst) for f in fs if "_1." in f]
check("rerun: no _1 duplicates", dups == [], str(dups))

# 16. Different file, same name -> gets _1
p = os.path.join(src, "sub", "edited.jpg")
make_jpeg(p, original="2019:07:04 12:00:00", modified="2001:01:01 00:00:00")
res3 = core.organize(job)
check("same name different content -> edited_1.jpg", os.path.exists(os.path.join(dst, "2019", "July", "edited_1.jpg")), f"{res3}")
check("only the new file transferred", res3.transferred == 1 and res3.skipped == 11)

# 17. Move mode with identical file already in dest -> source removed, counted skipped
job_mv = core.Job(source=src, photo_dest=dst, video_dest=dst, extensions=core.extensions_for("all"), delete_source=True)
res4 = core.organize(job_mv)
check("move: identical sources removed", not os.path.exists(os.path.join(src, "edited.jpg")), f"{res4}")
check("move: counted as skipped", res4.skipped == 12 and res4.transferred == 0 and res4.errors == [])

# 18. Separate video destination
src2 = os.path.join(tmp, "src2"); vdst = os.path.join(tmp, "vdst"); pdst = os.path.join(tmp, "pdst")
os.makedirs(src2)
make_jpeg(os.path.join(src2, "a.jpg"), original="2022:02:02 02:02:02")
make_mp4(os.path.join(src2, "b.mp4"), secs)
res5 = core.organize(core.Job(src2, pdst, vdst, core.extensions_for("all")))
check("separate dests", os.path.exists(os.path.join(pdst, "2022", "February", "a.jpg")) and os.path.exists(os.path.join(vdst, "2021", "August", "b.mp4")), f"{res5}")

# 19. Error is captured, not swallowed
src3 = os.path.join(tmp, "src3"); os.makedirs(src3)
make_jpeg(os.path.join(src3, "ok.jpg"), original="2022:02:02 02:02:02")
locked_dst = os.path.join(tmp, "locked")
os.makedirs(locked_dst, mode=0o500)
res6 = core.organize(core.Job(src3, locked_dst, locked_dst, core.extensions_for("all")))
check("permission error captured", len(res6.errors) == 1 and res6.processed == 1, str(res6.errors))
os.chmod(locked_dst, 0o700)

# 20. Cancel
src4 = os.path.join(tmp, "src4"); os.makedirs(src4)
for i in range(4):
    make_jpeg(os.path.join(src4, f"c{i}.jpg"), original="2022:02:02 02:02:02")
calls = []
res7 = core.organize(core.Job(src4, dst, dst, core.extensions_for("all")), progress=lambda a, b, c: calls.append(a), should_cancel=lambda: len(calls) >= 2)
check("cancel stops early", res7.cancelled and res7.processed == 2, f"{res7.processed}")

# 21. validate_paths
check("validate same", core.validate_paths(src, [src]) is not None)
check("validate inside", core.validate_paths(src, [os.path.join(src, "x")]) is not None)
check("validate ok", core.validate_paths(src, [dst, ""]) is None)
check("validate missing", core.validate_paths(os.path.join(tmp, "nope"), [dst]) is not None)

# 22. Logging
lp = core.configure_logging()
check("log path", lp is not None and lp.endswith("photo_organizer.log"), str(lp))
core.organize(core.Job(src3, dst, dst, core.extensions_for("all")))
with open(lp, encoding="utf-8") as f:
    txt = f.read()
check("log written", "Done:" in txt)

print()
print("FAILURES:", fails if fails else "none")
sys.exit(1 if fails else 0)
