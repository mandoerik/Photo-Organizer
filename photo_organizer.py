"""
Photo & Video Organizer
------------------
A professional media organization tool that automatically sorts photos and videos
into a structured year/month folder hierarchy based on their creation dates.

Features:
- Organizes photos and videos by date taken
- Optional separate processing for photos and videos
- Creates year/month folder structure automatically
- Supports multiple media formats (JPG, PNG, GIF, HEIC, WEBP, TIFF, MP4, MOV, AVI, ...)
- Maintains original file metadata
- Skips files that already exist in the destination (content compared, not just name)
- Supports English and Swedish folder naming
- Option to remove source files after organization
- Modern CustomTkinter UI with dark/light mode
"""

import locale
import os
import subprocess
import sys
import threading
import time

import customtkinter as ctk
from tkinter import filedialog, StringVar, BooleanVar

import organizer_core as core


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

        # App information
        self.app_info = {
            'name': 'Photo & Video Organizer',
            'version': '2.1',
            'year': '2026',
            'company': 'Express it Vendelso AB',
            'email': 'info@express-it.se'
        }

        # Cancellation flag (read by the worker thread between files)
        self.cancel_flag = False

        # Result of the last run, for the error dialog
        self.last_result = None
        self.log_path = core.configure_logging()

        # Background file counting: only the latest scan may update the UI
        self._count_generation = 0
        self._last_progress_post = 0.0

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

        self._build_ui()
        self.detect_system_language()

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

        # Shown only after a run that had failures
        self.errors_button = ctk.CTkButton(
            inner, text="Show errors", width=110, height=28,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", border_width=1,
            border_color=COLORS["error"], hover_color=COLORS["subtle_dark"],
            command=self.show_errors_dialog,
        )
        self.errors_button.grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.errors_button.grid_remove()

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

    # -- Error dialog ----------------------------------------------------------

    def show_errors_dialog(self):
        result = self.last_result
        if not result or not result.errors:
            return

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Files that could not be organized")
        dialog.geometry("640x420")
        dialog.transient(self.root)

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 640) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 420) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog, text=f"{len(result.errors)} file(s) failed",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(16, 6))

        box = ctk.CTkTextbox(dialog, font=ctk.CTkFont(size=12), wrap="none")
        box.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        for path, message in result.errors:
            box.insert("end", f"{path}\n    {message}\n")
        box.configure(state="disabled")

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 16))
        if self.log_path:
            ctk.CTkLabel(
                footer, text=f"Full log: {self.log_path}",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_secondary_dark"],
            ).pack(side="left")
            ctk.CTkButton(
                footer, text="Open log", width=90, height=30,
                command=self._open_log,
            ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            footer, text="Close", width=90, height=30, command=dialog.destroy,
        ).pack(side="right")

    def _open_log(self):
        if not self.log_path or not os.path.exists(self.log_path):
            return
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", self.log_path])
            elif sys.platform == "win32":
                os.startfile(self.log_path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", self.log_path])
        except Exception:
            pass

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
        """Count matching files in a background thread so a large source
        folder (NAS, external drive) does not freeze the window."""
        source = self.source_path.get()
        if not source:
            return
        extensions = core.extensions_for(self.file_type_selection.get())

        self._count_generation += 1
        generation = self._count_generation
        self.counter_var.set("Counting files...")

        def _count():
            try:
                total = len(core.collect_files(source, extensions))
            except Exception:
                total = 0

            def _apply():
                if generation == self._count_generation:
                    self.counter_var.set(f"0 / {total} files")
            self.root.after(0, _apply)

        threading.Thread(target=_count, daemon=True).start()

    # -- Organization ----------------------------------------------------------

    def cancel_organization(self):
        self.cancel_flag = True
        self.status_var.set("Cancelling...")
        self.cancel_button.configure(state="disabled")

    def _build_job(self):
        """Snapshot every setting on the main thread into a core.Job.

        Tk variables must not be read from the worker thread, so all the
        worker ever sees is this plain object.
        """
        selection = self.file_type_selection.get()
        photo_dest = self.photo_dest_path.get()
        video_dest = self.video_dest_path.get() if self.separate_videos.get() else photo_dest
        return core.Job(
            source=self.source_path.get(),
            photo_dest=photo_dest,
            video_dest=video_dest,
            extensions=core.extensions_for(selection),
            language=self.language_var.get(),
            delete_source=self.delete_files.get(),
        )

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

        job = self._build_job()
        error = core.validate_paths(job.source, [job.photo_dest, job.video_dest])
        if error:
            self.status_var.set(f"Error: {error}")
            return

        self.cancel_flag = False
        self.last_result = None
        self.errors_button.grid_remove()
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.status_var.set("Starting...")
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color=COLORS["accent"])

        thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        thread.start()

    # Worker-thread callbacks. Everything that touches a widget is handed to
    # the main thread via root.after().

    def _on_progress(self, processed, total, filename):
        now = time.monotonic()
        if processed < total and now - self._last_progress_post < 0.05:
            return  # at most ~20 UI updates per second
        self._last_progress_post = now

        def _do():
            self.progress_bar.set(processed / total if total else 0)
            self.counter_var.set(f"{processed} / {total} files")
            self.status_var.set(f"Processing: {filename}")
        self.root.after(0, _do)

    def _run_job(self, job):
        try:
            result = core.organize(
                job,
                progress=self._on_progress,
                should_cancel=lambda: self.cancel_flag,
            )
        except Exception as e:  # defensive: never let the thread die silently
            core.log.exception("Unexpected failure")
            result = core.Result(errors=[("(run aborted)", f"{type(e).__name__}: {e}")])
        self.root.after(0, lambda: self._finish(job, result))

    def _finish(self, job, result):
        self.last_result = result
        self.progress_bar.set(result.processed / result.total if result.total else 0)
        self.counter_var.set(f"{result.processed} / {result.total} files")
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")

        if result.total == 0 and not result.errors:
            self.status_var.set("No matching files found.")
            return

        if result.cancelled:
            self.status_var.set("Cancelled.")
            self.progress_bar.configure(progress_color=COLORS["warning"])
            return

        action = "moved" if job.delete_source else "copied"
        parts = [f"{result.transferred} files {action}"]
        if result.skipped:
            parts.append(f"{result.skipped} already in destination")
        if result.errors:
            parts.append(f"{len(result.errors)} failed")
        message = "Done! " + ", ".join(parts) + "."
        if result.errors:
            self.errors_button.grid()
            self.progress_bar.configure(progress_color=COLORS["warning"])
            if self.log_path:
                message += f" Log: {self.log_path}"
        else:
            self.progress_bar.configure(progress_color=COLORS["success"])
        self.status_var.set(message)

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
