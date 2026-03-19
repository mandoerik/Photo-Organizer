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
- Modern CustomTkinter UI with dark/light mode
"""

import locale
import os
import shutil
import sys
import threading
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, StringVar, BooleanVar


# --- Color Palette ---
COLORS = {
    "accent": "#4A90D9",
    "accent_hover": "#3A7BC8",
    "success": "#27AE60",
    "warning": "#F39C12",
    "error": "#E74C3C",
    "card_dark": "#1E1E2E",
    "card_light": "#FFFFFF",
    "subtle_dark": "#2A2A3C",
    "subtle_light": "#F0F2F5",
    "border_dark": "#3A3A4C",
    "border_light": "#D1D5DB",
    "text_secondary_dark": "#8B8FA3",
    "text_secondary_light": "#6B7280",
}


class PhotoOrganizerApp:
    def __init__(self):
        # Theme & appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Photo & Video Organizer")
        self.root.geometry("720x860")
        self.root.minsize(680, 820)

        # Lazy load PIL (heavy dependency)
        self._PIL = None

        # App information
        self.app_info = {
            'name': 'Photo & Video Organizer',
            'version': '2.0',
            'year': '2024',
            'company': 'Express it Vendelso AB',
            'email': 'info@express-it.se'
        }

        # Cancellation flag
        self.cancel_flag = False

        # Supported file types
        self.photo_extensions = ('.jpg', '.jpeg', '.png', '.gif')
        self.video_extensions = ('.mp4', '.mov', '.avi')

        # Variables
        self.file_type_selection = StringVar(value='all')
        self.language_var = StringVar(value='English')
        self.source_path = StringVar()
        self.photo_dest_path = StringVar()
        self.video_dest_path = StringVar()
        self.separate_videos = BooleanVar(value=False)
        self.delete_files = BooleanVar(value=False)
        self.status_var = StringVar(value="Ready")
        self.counter_var = StringVar(value="0 / 0 files")

        # Month translations
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

        # Counters
        self.processed_files = 0
        self.total_files = 0

        self._build_ui()
        self.detect_system_language()

    def _load_pil(self):
        """Lazy load PIL only when needed"""
        if self._PIL is None:
            from PIL import Image
            self._PIL = Image

    # ------------------------------------------------------------------ UI --
    def _build_ui(self):
        """Build the complete modern UI."""
        # Main scrollable container
        self.main_frame = ctk.CTkScrollableFrame(
            self.root, fg_color="transparent",
        )
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        self.main_frame.columnconfigure(0, weight=1)

        row = 0

        # ---- Header bar ----
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=row, column=0, sticky="ew", pady=(0, 4))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="Photo & Video Organizer",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        # Theme toggle + About
        btn_group = ctk.CTkFrame(header, fg_color="transparent")
        btn_group.grid(row=0, column=1, sticky="e")

        self.theme_btn = ctk.CTkButton(
            btn_group, text="Light", width=70, height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", border_width=1,
            border_color=COLORS["border_dark"],
            hover_color=COLORS["subtle_dark"],
            command=self._toggle_theme,
        )
        self.theme_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_group, text="About", width=70, height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", border_width=1,
            border_color=COLORS["border_dark"],
            hover_color=COLORS["subtle_dark"],
            command=self.show_about_dialog,
        ).pack(side="left")

        row += 1

        # ---- Description ----
        desc_text = (
            "Automatically organize your photos and videos into a clean Year / Month "
            "folder structure based on when they were taken."
        )
        ctk.CTkLabel(
            self.main_frame, text=desc_text, wraplength=640,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary_dark"],
            justify="left",
        ).grid(row=row, column=0, sticky="w", pady=(0, 16))

        row += 1

        # ---- File Type Card ----
        row = self._card_file_type(row)

        # ---- Language Card ----
        row = self._card_language(row)

        # ---- Folders Card ----
        row = self._card_folders(row)

        # ---- Options Card ----
        row = self._card_options(row)

        # ---- Progress Card ----
        row = self._card_progress(row)

        # ---- Action Buttons ----
        self._action_buttons(row)

    # -- Cards -----------------------------------------------------------------

    def _make_card(self, parent, title, row):
        """Create a styled card frame with a title label."""
        card = ctk.CTkFrame(parent, corner_radius=12)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        card.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))
        return card

    def _card_file_type(self, row):
        card = self._make_card(self.main_frame, "File Type", row)

        seg = ctk.CTkSegmentedButton(
            card, values=["All Files", "Photos Only", "Videos Only"],
            command=self._on_filetype_segment,
            font=ctk.CTkFont(size=13),
        )
        seg.set("All Files")
        seg.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        self._filetype_seg = seg

        return row + 1

    def _on_filetype_segment(self, value):
        mapping = {"All Files": "all", "Photos Only": "photos", "Videos Only": "videos"}
        self.file_type_selection.set(mapping[value])
        self.update_file_type_selection()

    def _card_language(self, row):
        card = self._make_card(self.main_frame, "Folder Name Language", row)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        inner.columnconfigure(1, weight=1)

        self.lang_menu = ctk.CTkOptionMenu(
            inner, values=["English", "Swedish"],
            variable=self.language_var,
            width=160, height=32,
            font=ctk.CTkFont(size=13),
        )
        self.lang_menu.grid(row=0, column=0, sticky="w")

        self.detected_lang_label = ctk.CTkLabel(
            inner, text="Detected: —",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary_dark"],
        )
        self.detected_lang_label.grid(row=0, column=1, sticky="e")

        return row + 1

    def _card_folders(self, row):
        card = self._make_card(self.main_frame, "Folders", row)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        inner.columnconfigure(0, weight=1)

        r = 0

        # Source
        r = self._folder_row(inner, r, "Source Folder", self.source_path, self.browse_source)

        # Photo dest
        self._photo_dest_label = ctk.CTkLabel(inner, text="Destination Folder", font=ctk.CTkFont(size=13))
        self._photo_dest_label.grid(row=r, column=0, sticky="w", pady=(10, 4))
        r += 1
        prow = ctk.CTkFrame(inner, fg_color="transparent")
        prow.grid(row=r, column=0, sticky="ew")
        prow.columnconfigure(0, weight=1)
        self._photo_dest_entry = ctk.CTkEntry(prow, textvariable=self.photo_dest_path, height=36, font=ctk.CTkFont(size=13))
        self._photo_dest_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._photo_dest_btn = ctk.CTkButton(prow, text="Browse", width=90, height=36, command=self.browse_photo_dest)
        self._photo_dest_btn.grid(row=0, column=1)
        r += 1

        # Separate videos toggle
        self.sep_video_switch = ctk.CTkSwitch(
            inner, text="Separate video destination",
            variable=self.separate_videos,
            command=self.toggle_video_destination,
            font=ctk.CTkFont(size=13),
        )
        self.sep_video_switch.grid(row=r, column=0, sticky="w", pady=(12, 4))
        r += 1

        # Video dest
        self._video_dest_label = ctk.CTkLabel(inner, text="Video Destination Folder", font=ctk.CTkFont(size=13))
        self._video_dest_label.grid(row=r, column=0, sticky="w", pady=(6, 4))
        r += 1
        vrow = ctk.CTkFrame(inner, fg_color="transparent")
        vrow.grid(row=r, column=0, sticky="ew")
        vrow.columnconfigure(0, weight=1)
        self._video_dest_entry = ctk.CTkEntry(vrow, textvariable=self.video_dest_path, height=36, state="disabled", font=ctk.CTkFont(size=13))
        self._video_dest_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._video_dest_btn = ctk.CTkButton(vrow, text="Browse", width=90, height=36, command=self.browse_video_dest, state="disabled")
        self._video_dest_btn.grid(row=0, column=1)

        # Initially hide video dest row
        self._video_dest_label.grid_remove()
        vrow.grid_remove()
        self._video_row_frame = vrow

        return row + 1

    def _folder_row(self, parent, r, label, var, cmd):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=13)).grid(row=r, column=0, sticky="w", pady=(0, 4))
        r += 1
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.grid(row=r, column=0, sticky="ew")
        row_frame.columnconfigure(0, weight=1)
        ctk.CTkEntry(row_frame, textvariable=var, height=36, font=ctk.CTkFont(size=13)).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(row_frame, text="Browse", width=90, height=36, command=cmd).grid(row=0, column=1)
        return r + 1

    def _card_options(self, row):
        card = self._make_card(self.main_frame, "Options", row)

        self.delete_switch = ctk.CTkSwitch(
            card, text="Delete source files after organizing",
            variable=self.delete_files,
            font=ctk.CTkFont(size=13),
        )
        self.delete_switch.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

        return row + 1

    def _card_progress(self, row):
        card = self._make_card(self.main_frame, "Progress", row)
        card.columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        inner.columnconfigure(0, weight=1)

        # Counter
        self.counter_label = ctk.CTkLabel(
            inner, textvariable=self.counter_var,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary_dark"],
        )
        self.counter_label.grid(row=0, column=0, sticky="w", pady=(0, 6))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(inner, height=10, corner_radius=5)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        # Status
        self.status_label = ctk.CTkLabel(
            inner, textvariable=self.status_var,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary_dark"],
            wraplength=620, justify="left",
        )
        self.status_label.grid(row=2, column=0, sticky="w")

        return row + 1

    def _action_buttons(self, row):
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.grid(row=row, column=0, sticky="ew", pady=(4, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        self.start_button = ctk.CTkButton(
            btn_frame, text="Start Organizing", height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.start_organization,
        )
        self.start_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.cancel_button = ctk.CTkButton(
            btn_frame, text="Cancel", height=44,
            font=ctk.CTkFont(size=15),
            fg_color="transparent", border_width=1,
            border_color=COLORS["border_dark"],
            hover_color=COLORS["error"],
            state="disabled",
            command=self.cancel_organization,
        )
        self.cancel_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    # -- Theme toggle ----------------------------------------------------------

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="Dark")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="Light")

    # -- About dialog ----------------------------------------------------------

    def show_about_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("About")
        dialog.geometry("380x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center on parent
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 380) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 300) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog, text=self.app_info['name'],
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(30, 4))

        ctk.CTkLabel(
            dialog, text=f"Version {self.app_info['version']}",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary_dark"],
        ).pack(pady=(0, 20))

        ctk.CTkLabel(
            dialog,
            text=f"\u00A9 {self.app_info['year']} {self.app_info['company']}",
            font=ctk.CTkFont(size=13),
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            dialog, text="All rights reserved",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary_dark"],
        ).pack(pady=(0, 16))

        ctk.CTkLabel(
            dialog, text=self.app_info['email'],
            font=ctk.CTkFont(size=13),
            text_color=COLORS["accent"],
        ).pack(pady=(0, 20))

        ctk.CTkButton(
            dialog, text="Close", width=120, height=36,
            command=dialog.destroy,
        ).pack()

    # -- System language detection ---------------------------------------------

    def detect_system_language(self):
        try:
            system_locale = locale.getlocale()[0]
            if system_locale and system_locale.startswith('sv'):
                self.detected_language = 'Swedish'
            else:
                self.detected_language = 'English'
        except Exception:
            self.detected_language = 'English'

        self.language_var.set(self.detected_language)
        self.detected_lang_label.configure(text=f"Detected: {self.detected_language}")

    # -- File type selection ---------------------------------------------------

    def update_file_type_selection(self):
        selection = self.file_type_selection.get()

        # Photo destination visibility
        photo_state = "disabled" if selection == "videos" else "normal"
        self._photo_dest_label.configure(state=photo_state)
        self._photo_dest_entry.configure(state=photo_state)
        self._photo_dest_btn.configure(state=photo_state)

        # Video destination handling
        if selection == 'videos':
            self.separate_videos.set(True)
            self.sep_video_switch.configure(state="disabled")
            self._show_video_dest(True)
        elif selection == 'photos':
            self.separate_videos.set(False)
            self.sep_video_switch.configure(state="disabled")
            self._show_video_dest(False)
            self.video_dest_path.set('')
        else:
            self.sep_video_switch.configure(state="normal")
            self.toggle_video_destination()

        if self.source_path.get():
            self.update_file_count()

    def _show_video_dest(self, show):
        if show:
            self._video_dest_label.grid()
            self._video_row_frame.grid()
            self._video_dest_entry.configure(state="normal")
            self._video_dest_btn.configure(state="normal")
        else:
            self._video_dest_label.grid_remove()
            self._video_row_frame.grid_remove()
            self._video_dest_entry.configure(state="disabled")
            self._video_dest_btn.configure(state="disabled")

    def toggle_video_destination(self):
        show = self.separate_videos.get()
        self._show_video_dest(show)
        if not show:
            self.video_dest_path.set('')

    # -- Folder browsing -------------------------------------------------------

    def browse_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_path.set(folder)
            self.update_file_count()

    def browse_photo_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.photo_dest_path.set(folder)

    def browse_video_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.video_dest_path.set(folder)

    # -- File count ------------------------------------------------------------

    def update_file_count(self):
        source = self.source_path.get()
        if source:
            selection = self.file_type_selection.get()
            if selection == 'all':
                extensions = self.photo_extensions + self.video_extensions
            elif selection == 'photos':
                extensions = self.photo_extensions
            else:
                extensions = self.video_extensions

            self.total_files = sum(
                1 for root, _, files in os.walk(source)
                for f in files if f.lower().endswith(extensions)
            )
            self.processed_files = 0
            self.counter_var.set(f"0 / {self.total_files} files")

    # -- Media date extraction -------------------------------------------------

    def get_media_date(self, file_path):
        try:
            if file_path.lower().endswith(self.photo_extensions):
                self._load_pil()
                with self._PIL.open(file_path) as img:
                    exif = img.getexif()
                    if exif:
                        if 306 in exif:
                            date_str = exif[306]
                            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                        exif_ifd = exif.get_ifd(0x8769)
                        if exif_ifd and 36867 in exif_ifd:
                            date_str = exif_ifd[36867]
                            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')

            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp)
        except Exception as e:
            print(f"Error getting date for {file_path}: {e}")
            return datetime.now()

    def get_localized_month(self, date):
        english_month = date.strftime('%B')
        selected_language = self.language_var.get()
        return self.month_translations[selected_language][english_month]

    # -- Organization ----------------------------------------------------------

    def cancel_organization(self):
        self.cancel_flag = True
        self.status_var.set("Cancelling...")
        self.cancel_button.configure(state="disabled")

    def _validate_paths(self):
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
                self.status_var.set("Error: Source and destination cannot be the same.")
                return False
            if dest.startswith(source + os.sep):
                self.status_var.set("Error: Destination cannot be inside the source folder.")
                return False
            if source.startswith(dest + os.sep):
                self.status_var.set("Error: Source is inside the destination.")
                return False
        return True

    def start_organization(self):
        selection = self.file_type_selection.get()

        if not self.source_path.get():
            self.status_var.set("Please select a source folder.")
            return
        if selection in ('all', 'photos') and not self.photo_dest_path.get():
            self.status_var.set("Please select a destination folder.")
            return
        if (selection == 'videos' or (selection == 'all' and self.separate_videos.get())) and not self.video_dest_path.get():
            self.status_var.set("Please select a video destination folder.")
            return
        if not self._validate_paths():
            return

        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.status_var.set("Starting...")
        self.progress_bar.set(0)
        self.processed_files = 0

        thread = threading.Thread(target=self.organize_files, daemon=True)
        thread.start()

    def _update_progress(self, processed, total, filename, done=False, cancelled=False, errors=0):
        def _do():
            frac = processed / total if total else 0
            self.progress_bar.set(frac)
            self.counter_var.set(f"{processed} / {total} files")
            if cancelled:
                self.status_var.set("Cancelled.")
                self.progress_bar.configure(progress_color=COLORS["warning"])
                self.start_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")
            elif done:
                action = "moved" if self.delete_files.get() else "copied"
                err = f" ({errors} failed)" if errors else ""
                self.status_var.set(f"Done! {processed - errors} files {action}.{err}")
                self.progress_bar.configure(progress_color=COLORS["success"])
                self.start_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")
            else:
                self.status_var.set(f"Processing: {filename}")
                self.progress_bar.configure(progress_color=COLORS["accent"])
        self.root.after(0, _do)

    def organize_files(self):
        source = self.source_path.get()
        photo_dest = self.photo_dest_path.get()
        video_dest = self.video_dest_path.get() if self.separate_videos.get() else photo_dest
        should_delete = self.delete_files.get()

        self.cancel_flag = False

        selection = self.file_type_selection.get()
        if selection == 'all':
            extensions = self.photo_extensions + self.video_extensions
        elif selection == 'photos':
            extensions = self.photo_extensions
        else:
            extensions = self.video_extensions

        files = []
        for dirpath, _, filenames in os.walk(source):
            for filename in filenames:
                if filename.lower().endswith(extensions):
                    files.append(os.path.join(dirpath, filename))

        self.total_files = len(files)

        if self.total_files == 0:
            self.root.after(0, lambda: self.status_var.set("No matching files found."))
            self.root.after(0, lambda: self.start_button.configure(state="normal"))
            self.root.after(0, lambda: self.cancel_button.configure(state="disabled"))
            return

        self.processed_files = 0
        error_count = 0

        for file_path in files:
            if self.cancel_flag:
                self._update_progress(self.processed_files, self.total_files, '', cancelled=True)
                return

            try:
                is_video = file_path.lower().endswith(self.video_extensions)
                dest_base = video_dest if is_video else photo_dest

                date = self.get_media_date(file_path)
                month = self.get_localized_month(date)
                dest_dir = os.path.join(dest_base, str(date.year), month)
                os.makedirs(dest_dir, exist_ok=True)

                filename = os.path.basename(file_path)
                base, ext = os.path.splitext(filename)
                counter = 1
                dest_path = os.path.join(dest_dir, filename)
                while os.path.exists(dest_path):
                    dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                    counter += 1

                if should_delete:
                    shutil.move(file_path, dest_path)
                else:
                    shutil.copy2(file_path, dest_path)

            except Exception as e:
                print(f"Error {'moving' if should_delete else 'copying'} {file_path}: {e}")
                error_count += 1

            self.processed_files += 1
            self._update_progress(self.processed_files, self.total_files, os.path.basename(file_path))

        if not self.cancel_flag:
            self._update_progress(self.processed_files, self.total_files, '', done=True, errors=error_count)

    # -- Run -------------------------------------------------------------------

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    app = PhotoOrganizerApp()
    app.run()
