<div align="center">
  <h1>Photo-Organizer</h1>
  <p>A clean, intuitive tool for organizing your media files on macOS</p>
</div>

<table>
<tr>
<td width="70%">

## About
Photo Organizer is a lightweight Python tool that automatically organizes your photos and videos into a clean folder structure by date taken. It creates year/month folders, preserves metadata, and handles multiple media formats.

## Features
- 📁 Automatic year/month folder structure
- 📷 Support for JPG, PNG, GIF, MP4, MOV, AVI
- 🔍 Preserves original metadata
- 🔄 Handles duplicate filenames
- 🌐 Supports English and Swedish folder naming
- 🗑️ Optional cleanup of source files

## Organization Options
- **File Type Selection:**
  - Photos Only: Organize just your photos (JPG, PNG, GIF)
  - Videos Only: Organize just your videos (MP4, MOV, AVI)
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
1. Download the latest release from our [Releases](link-to-releases) page
2. Extract Photo-Organizer.zip
3. Move Photo Organizer.app to your Applications folder

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

</td>
<td width="30%">
<img src="https://github.com/user-attachments/assets/0afd8827-371d-4f81-810a-47e8b5a1ece9" alt="Photo Organizer Interface" />
</td>
</tr>
</table>
