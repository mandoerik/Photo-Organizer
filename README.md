<div align="center">
  <h1>Photo & Video Organizer</h1>
  <p>A clean, intuitive tool for organizing your media files on macOS and Windows</p>
</div>

<table>
<tr>
<td width="70%">

## About
Photo Organizer is a lightweight Python tool that automatically organizes your photos and videos into a clean folder structure by date taken. It creates year/month folders, preserves metadata, and handles multiple media formats.

## Features
- 📁 Automatic year/month folder structure
- 📷 Photos: JPG, PNG, GIF, HEIC/HEIF (iPhone), WEBP, TIFF, BMP
- 🎬 Videos: MP4, MOV, M4V, 3GP, AVI, MKV, WEBM
- 📅 Date taken from EXIF (photos) or the container's creation time (MP4/MOV), falling back to file modification time
- 🔍 Preserves original metadata
- 🔄 Skips files already present in the destination (content compared, not just name) and renames on real name clashes
- 🙈 Ignores hidden files such as macOS `._` sidecars
- 📝 Writes a log and lists any failed files in the app
- 🌐 Supports English and Swedish folder naming
- 🗑️ Optional cleanup of source files

## Organization Options
- **File Type Selection:**
  - Photos Only: Organize just your photos
  - Videos Only: Organize just your videos
  - All Files: Organize both photos and videos together

- **Destination Options:**
  - Single Destination: Send all media to one organized folder
  - Separate Destinations: Send photos and videos to different organized folders

- **Language Options:**
  - English month names (e.g., January/2024)
  - Swedish month names (e.g., Januari/2024)
  - Automatically detects system language

- **File Handling:**
  - Copy Only: Keep original files in source location
  - Move Files: Remove files from source after organizing

## Result Structure
```
destination_folder/
├── 2024/
│   ├── January/
│   │   ├── photo1.jpg
│   │   ├── photo2.png
│   │   └── video1.mp4
│   └── February/
│       ├── photo3.jpg
│       └── video2.mov
└── 2023/
    └── December/
        └── photo4.jpg
```

## Installation

### macOS
1. Download the latest release from our [Releases](https://github.com/mandoerik/Photo-Organizer/releases) page
2. Extract Photo & Video Organizer.zip
3. Move Photo Organizer.app to your Applications folder

### Windows
1. Download `PhotoOrganizer.exe` from the [Releases](https://github.com/mandoerik/Photo-Organizer/releases) page
2. Run the executable — no installation required

### Building from Source (Windows)
1. Install Python 3.10+ from [python.org](https://python.org)
2. Clone the repository and run `build_windows.bat`
3. The executable will be in the `dist/` folder

## Usage
1. Launch Photo Organizer
2. Select source folder containing your media files
3. Choose organization options:
   - Select file types to organize (Photos/Videos/All)
   - Choose destination folder(s)
   - Set language preference
   - Enable/disable source file cleanup
4. Click "Start Organization" to begin
5. Monitor progress in the status bar

Files whose date cannot be determined at all are placed in an `Unknown Date` / `Okänt datum` folder. A log of every run is written to `~/Library/Logs/Photo Organizer/` on macOS and `%LOCALAPPDATA%\PhotoOrganizer\Logs\` on Windows; if any file fails, a **Show errors** button appears with the details.

## Development
The logic lives in `organizer_core.py` (no GUI dependency) and the CustomTkinter window in `photo_organizer.py`. Run the tests with:

```bash
python tests/test_core.py
```

<img src="https://github.com/user-attachments/assets/49b17574-6bf4-4752-bfd2-76b7f1730748" alt="Photo & Video Organizer Interface" width="75%"/>


