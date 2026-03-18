"""
Photo & Video Organizer
------------------
A professional media organization tool that automatically sorts photos and videos
into a structured year/month folder hierarchy based on their creation dates.

Features:
- Organizes photos and videos by date taken
- Optional separate processing for photos and videos
- Creates year/month folder structure automatically
- Supports multiple media formats (JPG, PNG, GIF, MP4, MOV, AVI)
- Maintains original file metadata
- Handles duplicate filenames
- Supports English and Swedish folder naming
- Option to remove source files after organization
"""

import locale
import os
import shutil
import sys
import threading
from datetime import datetime
from tkinter import Tk, Toplevel, StringVar, BooleanVar, PhotoImage, N, W, E, S, BOTH
from tkinter import filedialog, ttk


class PhotoOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo & Video Organizer")
        self.root.minsize(800, 900)  # Set minimum size
        self.root.geometry("800x900")  # Set fixed starting size
        self.root.resizable(False, False)

        # Lazy load PIL (heavy dependency)
        self._PIL = None

        # App information
        self.app_info = {
            'name': 'Photo & Video Organizer',
            'version': '1.2',
            'year': '2024',
            'company': 'Express it Vendelso AB',
            'email': 'info@express-it.se'
        }

        # Add cancellation flag
        self.cancel_flag = False

        # Define supported file types
        self.photo_extensions = ('.jpg', '.jpeg', '.png', '.gif')
        self.video_extensions = ('.mp4', '.mov', '.avi')

        # Initialize file type selection
        self.file_type_selection = StringVar(value='all')

        # Define month translations
        self.month_translations = {
            'English': {
                'January': 'January', 'February': 'February', 'March': 'March',
                'April': 'April', 'May': 'May', 'June': 'June',
                'July': 'July', 'August': 'August', 'September': 'September',
                'October': 'October', 'November': 'November', 'December': 'December'
            },
            'Swedish': {
                'January': 'Januari', 'February': 'Februari', 'March': 'Mars',
                'April': 'April', 'May': 'Maj', 'June': 'Juni',
                'July': 'Juli', 'August': 'Augusti', 'September': 'September',
                'October': 'Oktober', 'November': 'November', 'December': 'December'
            }
        }

        # Initialize counters
        self.processed_files = 0
        self.total_files = 0

        self.setup_gui()
        self.detect_system_language()

    def _load_pil(self):
        """Lazy load PIL only when needed (heavy dependency)"""
        if self._PIL is None:
            from PIL import Image
            self._PIL = Image

    def setup_gui(self):
        # Create main container with padding
        self.main_container = ttk.Frame(self.root, padding="20")
        self.main_container.grid(row=0, column=0, sticky=(N, W, E, S))

        # Configure styles for a more modern look
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('SubHeader.TLabel', font=('Helvetica', 12))
        style.configure('Description.TLabel', font=('Helvetica', 11), wraplength=700)

        # Header and Description Frame
        header_frame = ttk.Frame(self.main_container)
        header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=(W, E))

        # Header container for title and about button
        header_container = ttk.Frame(header_frame)
        header_container.grid(row=0, column=0, sticky=(W, E))
        header_container.columnconfigure(1, weight=1)

        # App title
        ttk.Label(header_container, text="Photo & Video Organizer", style='Header.TLabel').grid(row=0, column=0, sticky=W)

        # About button
        about_button = ttk.Button(header_container, text="About", command=self.show_about_dialog, width=8)
        about_button.grid(row=0, column=1, sticky=E, padx=(0, 5))

        # Description box
        desc_frame = ttk.LabelFrame(header_frame, padding="15")
        desc_frame.grid(row=1, column=0, sticky=(W, E), pady=(10, 0))

        description_text = (
            "Automatically organize your photos and videos into a clean folder structure based on when they "
            "were taken. The app creates Year/Month folders and sorts your media files accordingly, making "
            "it easy to find and manage your memories. Simply select your source folder containing media "
            "files and choose where you want them organized."
        )

        ttk.Label(
            desc_frame,
            text=description_text,
            style='Description.TLabel'
        ).grid(row=0, column=0, sticky=(W, E))

        # File type selection frame
        filetype_frame = ttk.LabelFrame(self.main_container, text="File Type Selection", padding="10")
        filetype_frame.grid(row=1, column=0, columnspan=2, sticky=(W, E), pady=(0, 20))

        ttk.Radiobutton(
            filetype_frame,
            text="All Files (Photos and Videos)",
            variable=self.file_type_selection,
            value='all',
            command=self.update_file_type_selection
        ).grid(row=0, column=0, sticky=W, padx=5)

        ttk.Radiobutton(
            filetype_frame,
            text="Photos Only",
            variable=self.file_type_selection,
            value='photos',
            command=self.update_file_type_selection
        ).grid(row=0, column=1, sticky=W, padx=5)

        ttk.Radiobutton(
            filetype_frame,
            text="Videos Only",
            variable=self.file_type_selection,
            value='videos',
            command=self.update_file_type_selection
        ).grid(row=0, column=2, sticky=W, padx=5)

        # Language selection
        lang_frame = ttk.LabelFrame(self.main_container, text="Language Settings", padding="10")
        lang_frame.grid(row=2, column=0, columnspan=2, sticky=(W, E), pady=(0, 20))

        self.language_var = StringVar(value='English')
        ttk.Label(lang_frame, text="Folder Names Language:").grid(row=0, column=0, padx=5)
        self.lang_dropdown = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=['English', 'Swedish'],
            state='readonly'
        )
        self.lang_dropdown.grid(row=0, column=1, padx=5)

        # System language detection display
        self.language_label = ttk.Label(lang_frame, text="Detected language: ", style='SubHeader.TLabel')
        self.language_label.grid(row=0, column=2, padx=(20, 0))

        # Folder selection frame
        folder_frame = ttk.LabelFrame(self.main_container, text="Folder Selection", padding="10")
        folder_frame.grid(row=3, column=0, columnspan=2, sticky=(W, E), pady=(0, 20))

        # Source folder
        ttk.Label(folder_frame, text="Source Folder:").grid(row=0, column=0, sticky=W, pady=5)
        self.source_path = StringVar()
        ttk.Entry(folder_frame, textvariable=self.source_path, width=50).grid(row=1, column=0, padx=5)
        ttk.Button(folder_frame, text="Browse", command=self.browse_source).grid(row=1, column=1)

        # Photo destination folder — store references for toggling
        self.photo_dest_label = ttk.Label(folder_frame, text="Photo Destination Folder:")
        self.photo_dest_label.grid(row=2, column=0, sticky=W, pady=5)
        self.photo_dest_path = StringVar()
        self.photo_dest_entry = ttk.Entry(folder_frame, textvariable=self.photo_dest_path, width=50)
        self.photo_dest_entry.grid(row=3, column=0, padx=5)
        self.photo_dest_button = ttk.Button(folder_frame, text="Browse", command=self.browse_photo_dest)
        self.photo_dest_button.grid(row=3, column=1)

        # Separate videos checkbox
        self.separate_videos = BooleanVar()
        self.separate_videos.set(False)
        self.separate_videos_check = ttk.Checkbutton(
            folder_frame,
            text="Separate videos to different destination",
            variable=self.separate_videos,
            command=self.toggle_video_destination
        )
        self.separate_videos_check.grid(row=4, column=0, sticky=W, pady=5)

        # Video destination folder
        ttk.Label(folder_frame, text="Video Destination Folder:").grid(row=5, column=0, sticky=W, pady=5)
        self.video_dest_path = StringVar()
        self.video_dest_entry = ttk.Entry(folder_frame, textvariable=self.video_dest_path, width=50, state='disabled')
        self.video_dest_entry.grid(row=6, column=0, padx=5)
        self.video_dest_button = ttk.Button(folder_frame, text="Browse", command=self.browse_video_dest, state='disabled')
        self.video_dest_button.grid(row=6, column=1)

        # Options frame
        options_frame = ttk.LabelFrame(self.main_container, text="Options", padding="10")
        options_frame.grid(row=4, column=0, columnspan=2, sticky=(W, E), pady=(0, 20))

        # Delete files checkbox
        self.delete_files = BooleanVar()
        self.delete_files.set(False)
        ttk.Checkbutton(
            options_frame,
            text="Delete files from source after organizing",
            variable=self.delete_files
        ).grid(row=0, column=0, sticky=W)

        # Progress frame
        progress_frame = ttk.LabelFrame(self.main_container, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=2, sticky=(W, E))

        # File counter
        self.counter_var = StringVar(value="Files Processed: 0 / 0")
        ttk.Label(progress_frame, textvariable=self.counter_var).grid(row=0, column=0, sticky=W, pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(progress_frame, mode='determinate', length=600)
        self.progress.grid(row=1, column=0, columnspan=2, pady=5)

        # Status message
        self.status_var = StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.status_var, wraplength=600).grid(row=2, column=0, columnspan=2, pady=5)

        # Buttons frame
        buttons_frame = ttk.Frame(self.main_container)
        buttons_frame.grid(row=6, column=0, columnspan=2, pady=20)

        # Start button
        self.start_button = ttk.Button(buttons_frame, text="Start Organization", command=self.start_organization)
        self.start_button.grid(row=0, column=0, padx=5)

        # Cancel button
        self.cancel_button = ttk.Button(buttons_frame, text="Cancel", command=self.cancel_organization, state='disabled')
        self.cancel_button.grid(row=0, column=1, padx=5)

    def detect_system_language(self):
        """Detect system language"""
        try:
            system_locale = locale.getlocale()[0]
            if system_locale and system_locale.startswith('sv'):
                self.detected_language = 'Swedish'
            else:
                self.detected_language = 'English'
        except Exception:
            self.detected_language = 'English'

        # Set the dropdown to the detected language
        self.language_var.set(self.detected_language)
        self.language_label.config(text=f"Detected language: {self.detected_language}")

    def show_about_dialog(self):
        """Show the about dialog with app information"""
        about_dialog = Toplevel(self.root)
        about_dialog.title("About Photo & Video Organizer")
        about_dialog.geometry("400x300")
        about_dialog.resizable(False, False)

        # Make the dialog modal
        about_dialog.transient(self.root)
        about_dialog.grab_set()

        # Center the dialog on the main window
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 300) // 2
        about_dialog.geometry(f"+{x}+{y}")

        # Container frame with padding
        container = ttk.Frame(about_dialog, padding="20")
        container.pack(fill=BOTH, expand=True)

        # App name
        ttk.Label(
            container,
            text=self.app_info['name'],
            font=('Helvetica', 16, 'bold')
        ).pack(pady=(0, 5))

        # Version
        ttk.Label(
            container,
            text=f"Version {self.app_info['version']}",
            font=('Helvetica', 12, 'italic')
        ).pack(pady=(0, 20))

        # Copyright notice
        ttk.Label(
            container,
            text=f"© {self.app_info['year']} {self.app_info['company']}",
            font=('Helvetica', 12)
        ).pack(pady=(0, 5))

        ttk.Label(
            container,
            text="All rights reserved",
            font=('Helvetica', 12)
        ).pack(pady=(0, 20))

        # Contact information
        ttk.Label(
            container,
            text="Contact:",
            font=('Helvetica', 12)
        ).pack(pady=(0, 5))

        ttk.Label(
            container,
            text=self.app_info['email'],
            font=('Helvetica', 12)
        ).pack(pady=(0, 20))

        # Close button
        ttk.Button(
            container,
            text="Close",
            command=about_dialog.destroy,
            width=15
        ).pack(pady=(10, 0))

    def update_file_type_selection(self):
        """Update UI based on file type selection"""
        selection = self.file_type_selection.get()

        # Toggle photo destination widgets directly via stored references
        photo_state = 'disabled' if selection == 'videos' else 'normal'
        self.photo_dest_label.configure(state=photo_state)
        self.photo_dest_entry.configure(state=photo_state)
        self.photo_dest_button.configure(state=photo_state)

        # Update video destination fields
        if selection == 'videos':
            self.separate_videos.set(True)
            self.separate_videos_check.configure(state='disabled')
            self.video_dest_entry.configure(state='normal')
            self.video_dest_button.configure(state='normal')
        elif selection == 'photos':
            self.separate_videos.set(False)
            self.separate_videos_check.configure(state='disabled')
            self.video_dest_entry.configure(state='disabled')
            self.video_dest_button.configure(state='disabled')
            self.video_dest_path.set('')
        else:  # all
            self.separate_videos_check.configure(state='normal')
            self.toggle_video_destination()

        # Update file count
        if self.source_path.get():
            self.update_file_count()

    def toggle_video_destination(self):
        """Enable/disable video destination selection based on checkbox"""
        state = 'normal' if self.separate_videos.get() else 'disabled'
        self.video_dest_entry.config(state=state)
        self.video_dest_button.config(state=state)

        # Clear video destination path if disabled
        if state == 'disabled':
            self.video_dest_path.set('')

    def browse_source(self):
        """Open dialog to select source folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.source_path.set(folder)
            self.update_file_count()

    def browse_photo_dest(self):
        """Open dialog to select photo destination folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.photo_dest_path.set(folder)

    def browse_video_dest(self):
        """Open dialog to select video destination folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.video_dest_path.set(folder)

    def update_file_count(self):
        """Update the total file count when source folder is selected"""
        source = self.source_path.get()
        if source:
            selection = self.file_type_selection.get()
            if selection == 'all':
                extensions = self.photo_extensions + self.video_extensions
            elif selection == 'photos':
                extensions = self.photo_extensions
            else:  # videos
                extensions = self.video_extensions

            self.total_files = sum(1 for root, _, files in os.walk(source)
                                 for f in files if f.lower().endswith(extensions))
            self.processed_files = 0
            self.counter_var.set(f"Files Processed: {self.processed_files} / {self.total_files}")

    def get_media_date(self, file_path):
        """Get the creation date of a media file"""
        try:
            # Try to get EXIF data for photos
            if file_path.lower().endswith(self.photo_extensions):
                self._load_pil()
                with self._PIL.open(file_path) as img:
                    exif = img.getexif()
                    if exif:
                        # Check root IFD for DateTime (tag 306)
                        if 306 in exif:
                            date_str = exif[306]
                            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                        # Check Exif sub-IFD for DateTimeOriginal (tag 36867)
                        exif_ifd = exif.get_ifd(0x8769)
                        if exif_ifd and 36867 in exif_ifd:
                            date_str = exif_ifd[36867]
                            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')

            # Fall back to file modification time
            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp)

        except Exception as e:
            print(f"Error getting date for {file_path}: {str(e)}")
            # Return current date if all methods fail
            return datetime.now()

    def get_localized_month(self, date):
        """Get month name in current language"""
        english_month = date.strftime('%B')
        selected_language = self.language_var.get()
        return self.month_translations[selected_language][english_month]

    def cancel_organization(self):
        """Cancel the organization process"""
        self.cancel_flag = True
        self.status_var.set("Cancelling... Please wait.")
        self.cancel_button['state'] = 'disabled'

    def _validate_paths(self):
        """Validate source and destination paths before organizing."""
        source = os.path.realpath(self.source_path.get())

        if not os.path.isdir(source):
            self.status_var.set("Error: Source folder does not exist.")
            return False

        photo_dest = os.path.realpath(self.photo_dest_path.get()) if self.photo_dest_path.get() else ''
        video_dest = os.path.realpath(self.video_dest_path.get()) if self.video_dest_path.get() else ''

        for dest in (photo_dest, video_dest):
            if not dest:
                continue
            if source == dest:
                self.status_var.set("Error: Source and destination folders cannot be the same.")
                return False
            if dest.startswith(source + os.sep):
                self.status_var.set("Error: Destination folder cannot be inside the source folder.")
                return False
            if source.startswith(dest + os.sep):
                self.status_var.set("Error: Source folder is inside the destination. Files could be reorganized into themselves.")
                return False
        return True

    def start_organization(self):
        """Start the organization process in a separate thread"""
        selection = self.file_type_selection.get()

        if not self.source_path.get():
            self.status_var.set("Please select source folder")
            return

        if selection in ['all', 'photos'] and not self.photo_dest_path.get():
            self.status_var.set("Please select photo destination folder")
            return

        if (selection == 'videos' or
            (selection == 'all' and self.separate_videos.get())) and not self.video_dest_path.get():
            self.status_var.set("Please select video destination folder")
            return

        if not self._validate_paths():
            return

        self.start_button['state'] = 'disabled'
        self.cancel_button['state'] = 'normal'
        self.status_var.set("Starting organization...")
        self.progress['value'] = 0
        self.processed_files = 0

        # Run in separate thread to keep GUI responsive
        thread = threading.Thread(target=self.organize_files)
        thread.daemon = True
        thread.start()

    def _update_progress(self, processed, total, filename, done=False, cancelled=False, errors=0):
        """Schedule a UI update on the main thread (thread-safe)."""
        def _do_update():
            self.progress['value'] = processed
            self.counter_var.set(f"Files Processed: {processed} / {total}")
            if cancelled:
                self.status_var.set("Organization cancelled.")
                self.start_button['state'] = 'normal'
                self.cancel_button['state'] = 'disabled'
            elif done:
                action_text = "moved" if self.delete_files.get() else "copied"
                error_text = f" ({errors} failed)" if errors else ""
                self.status_var.set(f"Organization completed! {processed - errors} files have been {action_text}.{error_text}")
                self.start_button['state'] = 'normal'
                self.cancel_button['state'] = 'disabled'
            else:
                self.status_var.set(f"Processing: {filename}")
        self.root.after(0, _do_update)

    def organize_files(self):
        """Main function to organize files"""
        source = self.source_path.get()
        photo_dest = self.photo_dest_path.get()
        video_dest = self.video_dest_path.get() if self.separate_videos.get() else photo_dest
        should_delete = self.delete_files.get()

        # Reset cancel flag
        self.cancel_flag = False

        # Get list of media files based on selection
        selection = self.file_type_selection.get()
        if selection == 'all':
            extensions = self.photo_extensions + self.video_extensions
        elif selection == 'photos':
            extensions = self.photo_extensions
        else:  # videos
            extensions = self.video_extensions

        files = []
        for dirpath, _, filenames in os.walk(source):
            for filename in filenames:
                if filename.lower().endswith(extensions):
                    files.append(os.path.join(dirpath, filename))

        self.total_files = len(files)

        if self.total_files == 0:
            self.root.after(0, lambda: self.status_var.set("No matching files found in source folder."))
            self.root.after(0, lambda: self.start_button.configure(state='normal'))
            self.root.after(0, lambda: self.cancel_button.configure(state='disabled'))
            return

        self.root.after(0, lambda: self.progress.configure(maximum=self.total_files))
        self.processed_files = 0
        error_count = 0

        for file_path in files:
            # Check if cancellation was requested
            if self.cancel_flag:
                self._update_progress(self.processed_files, self.total_files, '', cancelled=True)
                return

            try:
                # Determine if file is video or photo
                is_video = file_path.lower().endswith(self.video_extensions)
                dest_base = video_dest if is_video else photo_dest

                # Get date from file
                date = self.get_media_date(file_path)

                # Create year/month folders with localized month name
                month = self.get_localized_month(date)
                year_month = f"{date.year}/{month}"
                dest_dir = os.path.join(dest_base, year_month)
                os.makedirs(dest_dir, exist_ok=True)

                # Handle duplicate filenames
                filename = os.path.basename(file_path)
                base, ext = os.path.splitext(filename)
                counter = 1
                dest_path = os.path.join(dest_dir, filename)
                while os.path.exists(dest_path):
                    dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                    counter += 1

                # Move or copy file based on checkbox selection
                if should_delete:
                    shutil.move(file_path, dest_path)
                else:
                    shutil.copy2(file_path, dest_path)

            except Exception as e:
                print(f"Error {'moving' if should_delete else 'copying'} {file_path}: {str(e)}")
                error_count += 1

            # Update progress (thread-safe) — always increment, even on error
            self.processed_files += 1
            self._update_progress(self.processed_files, self.total_files, os.path.basename(file_path))

        if not self.cancel_flag:
            self._update_progress(self.processed_files, self.total_files, '', done=True, errors=error_count)


if __name__ == "__main__":
    root = Tk()
    try:
        if sys.platform == "darwin":  # macOS
            # On macOS, the .icns file should be part of the app bundle
            # The icon will be picked up automatically when bundled
            pass
        else:
            # For Windows/Linux, using .png as fallback
            root.wm_iconphoto(True, PhotoImage(file="photo_organizer.png"))
    except Exception:
        pass  # If icon loading fails, continue without an icon

    app = PhotoOrganizerApp(root)
    root.mainloop()
