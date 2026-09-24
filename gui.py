import os
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import customtkinter as ctk

# Ensure sorter_engine can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sorter_engine

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundled = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundled):
            return bundled
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

# Setup CustomTkinter Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Smooth Color Animation Utilities
def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c * 2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(
        max(0, min(255, int(round(rgb[0])))),
        max(0, min(255, int(round(rgb[1])))),
        max(0, min(255, int(round(rgb[2]))))
    )

def lerp_color(c1, c2, t):
    if c1 and c2 and c1.startswith('#') and c2.startswith('#'):
        try:
            rgb1 = hex_to_rgb(c1)
            rgb2 = hex_to_rgb(c2)
            res = tuple(rgb1[i] + (rgb2[i] - rgb1[i]) * t for i in range(3))
            return rgb_to_hex(res)
        except Exception:
            pass
    return c2 if t > 0.5 else c1

class AnimatedCTkButton(ctk.CTkButton):
    """
    Modern Smooth-Hover Button with:
    - 60+ FPS ease-out color interpolation for fill and border
    - Luminous glowing border accent on hover
    - Tactile micro-press feedback on click
    - Fluid pointer tracking without stutter
    """
    def __init__(self, master=None, hover_border_color=None, **kwargs):
        self._target_hover_border = hover_border_color or kwargs.get('hover_color', '#3b82f6')
        kwargs['hover'] = False  # Disable instantaneous snapping
        if 'border_width' not in kwargs and hover_border_color:
            kwargs['border_width'] = 1
        super().__init__(master, **kwargs)

        try:
            self.configure(cursor='hand2')
        except Exception:
            pass

        self._anim_progress = 0.0
        self._anim_timer = None
        self._is_pressed = False
        self._base_fg = kwargs.get('fg_color', '#2563eb')
        self._target_hover_fg = kwargs.get('hover_color', '#3b82f6')
        self._base_border = kwargs.get('border_color', '#27272a')

    def _is_pointer_inside(self):
        try:
            x, y = self.winfo_pointerxy()
            wx = self.winfo_rootx()
            wy = self.winfo_rooty()
            ww = self.winfo_width()
            wh = self.winfo_height()
            return (wx <= x <= wx + ww) and (wy <= y <= wy + wh)
        except Exception:
            return False

    def _on_enter(self, event=None):
        self._mouse_inside = True
        if self._state == 'disabled':
            return
        if self._anim_timer:
            self.after_cancel(self._anim_timer)
            self._anim_timer = None
        self._step_to(1.0)

    def _on_leave(self, event=None):
        if not self._is_pointer_inside():
            self._mouse_inside = False
            self._is_pressed = False
            if self._state == 'disabled':
                return
            if self._anim_timer:
                self.after_cancel(self._anim_timer)
                self._anim_timer = None
            self._step_to(0.0)

    def _on_press(self, event=None):
        self._is_pressed = True
        if self._state == 'disabled':
            return
        press_fg = lerp_color(self._target_hover_fg, '#000000', 0.22)
        self._apply_visuals(press_fg, self._target_hover_border)
        super()._on_press(event)

    def _on_release(self, event=None):
        self._is_pressed = False
        super()._on_release(event)
        if self._state == 'disabled':
            return
        if self._is_pointer_inside():
            self._step_to(1.0)
        else:
            self._step_to(0.0)

    def _step_to(self, target):
        step_delta = 0.20
        if abs(self._anim_progress - target) <= step_delta:
            self._anim_progress = target
        elif self._anim_progress < target:
            self._anim_progress += step_delta
        else:
            self._anim_progress -= step_delta

        t = self._anim_progress
        # Smooth quadratic ease-out curve
        eased = 1 - (1 - t) * (1 - t) if target == 1.0 else t * t

        fg = lerp_color(self._base_fg, self._target_hover_fg, eased)
        border = lerp_color(self._base_border, self._target_hover_border, eased)
        self._apply_visuals(fg, border)

        if self._anim_progress != target:
            self._anim_timer = self.after(14, lambda: self._step_to(target))
        else:
            self._anim_timer = None

    def _apply_visuals(self, fg, border):
        try:
            self._canvas.itemconfig('inner_parts', outline=fg, fill=fg)
            if self._border_width > 0:
                self._canvas.itemconfig('border_parts', outline=border, fill=border)
            if self._text_label is not None:
                self._text_label.configure(bg=fg)
            if self._image_label is not None:
                self._image_label.configure(bg=fg)
        except Exception:
            pass

    def configure(self, require_redraw=False, **kwargs):
        if 'fg_color' in kwargs and kwargs['fg_color'] is not None:
            self._base_fg = kwargs['fg_color']
        if 'hover_color' in kwargs and kwargs['hover_color'] is not None:
            self._target_hover_fg = kwargs['hover_color']
        if 'border_color' in kwargs and kwargs['border_color'] is not None:
            self._base_border = kwargs['border_color']
        if 'hover_border_color' in kwargs and kwargs['hover_border_color'] is not None:
            self._target_hover_border = kwargs.pop('hover_border_color')

        super().configure(require_redraw=require_redraw, **kwargs)

        if 'state' in kwargs:
            if kwargs['state'] == 'disabled':
                if self._anim_timer:
                    self.after_cancel(self._anim_timer)
                    self._anim_timer = None
                self._anim_progress = 0.0

def attach_card_hover(card, normal_bg="#18181b", hover_bg="#202024", normal_border="#27272a", hover_border="#3b82f6"):
    """Smooth glowing border and subtle background transition for cards"""
    state = {"progress": 0.0, "timer": None}

    def is_inside():
        try:
            x, y = card.winfo_pointerxy()
            wx = card.winfo_rootx()
            wy = card.winfo_rooty()
            ww = card.winfo_width()
            wh = card.winfo_height()
            return (wx <= x <= wx + ww) and (wy <= y <= wy + wh)
        except Exception:
            return False

    def step(target):
        delta = 0.20
        if abs(state["progress"] - target) <= delta:
            state["progress"] = target
        elif state["progress"] < target:
            state["progress"] += delta
        else:
            state["progress"] -= delta

        t = state["progress"]
        eased = 1 - (1 - t) * (1 - t) if target == 1.0 else t * t
        cur_bg = lerp_color(normal_bg, hover_bg, eased)
        cur_border = lerp_color(normal_border, hover_border, eased)
        try:
            card.configure(fg_color=cur_bg, border_color=cur_border)
        except Exception:
            pass

        if state["progress"] != target:
            state["timer"] = card.after(14, lambda: step(target))
        else:
            state["timer"] = None

    def on_enter(e=None):
        if state["timer"]:
            card.after_cancel(state["timer"])
            state["timer"] = None
        step(1.0)

    def on_leave(e=None):
        if not is_inside():
            if state["timer"]:
                card.after_cancel(state["timer"])
                state["timer"] = None
            step(0.0)

    def bind_recursive(w):
        w.bind("<Enter>", on_enter, add="+")
        w.bind("<Leave>", on_leave, add="+")
        for child in w.winfo_children():
            bind_recursive(child)

    bind_recursive(card)

def attach_entry_glow(entry, normal_border="#3f3f46", focus_border="#3b82f6"):
    """Smooth glowing border transition for input fields on hover and focus"""
    state = {"progress": 0.0, "timer": None, "focused": False}

    def step(target):
        delta = 0.22
        if abs(state["progress"] - target) <= delta:
            state["progress"] = target
        elif state["progress"] < target:
            state["progress"] += delta
        else:
            state["progress"] -= delta

        t = state["progress"]
        eased = 1 - (1 - t) * (1 - t) if target == 1.0 else t * t
        cur_border = lerp_color(normal_border, focus_border, eased)
        try:
            entry.configure(border_color=cur_border)
        except Exception:
            pass

        if state["progress"] != target:
            state["timer"] = entry.after(14, lambda: step(target))
        else:
            state["timer"] = None

    def on_focus_in(e=None):
        state["focused"] = True
        if state["timer"]:
            entry.after_cancel(state["timer"])
            state["timer"] = None
        step(1.0)

    def on_focus_out(e=None):
        state["focused"] = False
        if state["timer"]:
            entry.after_cancel(state["timer"])
            state["timer"] = None
        step(0.0)

    entry.bind("<FocusIn>", on_focus_in, add="+")
    entry.bind("<FocusOut>", on_focus_out, add="+")

CATEGORY_COLORS = {
    "Kuliah": "#a78bfa",
    "Coding": "#38bdf8",
    "Games": "#f43f5e",
    "Documents": "#60a5fa",
    "Archives": "#fbbf24",
    "Images": "#34d399",
    "Videos": "#fb7185",
    "Audio": "#c084fc",
    "Installers": "#fb923c",
    "Design_3D": "#2dd4bf",
    "Fonts": "#94a3b8",
    "Torrents": "#10b981",
    "Folders": "#a1a1aa",
    "Others": "#71717a"
}

CATEGORY_ICONS = {
    "Kuliah": "🎓",
    "Coding": "💻",
    "Games": "🎮",
    "Documents": "📄",
    "Archives": "📦",
    "Images": "🖼️",
    "Videos": "🎬",
    "Audio": "🎵",
    "Installers": "⚙️",
    "Design_3D": "🧊",
    "Fonts": "🔤",
    "Torrents": "🧲",
    "Folders": "📁",
    "Others": "📌"
}

TRANSLATIONS = {
    "ID": {
        "window_title": "KQ Sortify - Intelligent File Organizer",
        "subtitle": "PENGATUR FILE OTOMATIS (KULIAH • CODING • GAMES • DOKUMEN)",
        "rules_btn": "⚙️ Aturan Kategori",
        "undo_btn": "↩️ Undo Terakhir",
        "undo_count": "↩️ Undo ({count} File)",
        "path_title": "📁 PATH FOLDER YANG INGIN DIRAPIKAN",
        "path_placeholder": "Ketik atau tempel path folder di sini (misal: C:\\Users\\...\\Downloads)",
        "browse_btn": "📂 Cari Folder...",
        "scan_btn": "🔍 Pindai File",
        "scanning": "Memindai...",
        "mode_in_place": "Rapikan langsung di folder ini (Buat subfolder Kuliah, Coding, Games, dll.)",
        "mode_subfolder": "Pindahkan ke subfolder '/Organized/'",
        "stat_total_files": "TOTAL FILE",
        "stat_total_size": "TOTAL UKURAN",
        "stat_categories": "KATEGORI DETEKSI",
        "stat_selected": "FILE TERPILIH",
        "all_files": "Semua File",
        "select_all": "Pilih Semua",
        "search_placeholder": "🔍 Cari nama file / ekstensi...",
        "dry_run_badge": "🛡️ Mode Aman (Dry-Run Aktif)",
        "organize_btn": "⚡ Rapikan Sekarang ({count} File)",
        "organizing": "Memindahkan...",
        "col_select": "Pilih",
        "col_name": "Nama File",
        "col_cat": "Kategori",
        "col_dest": "Folder Tujuan",
        "col_size": "Ukuran",
        "col_date": "Tanggal",
        "status_ready": "Siap. Masukkan atau pilih path folder di atas untuk mulai merapikan.",
        "status_scanning": "Memindai isi folder: {folder} ...",
        "status_scan_done": "Pemindaian selesai: {count} file ditemukan ({size}).",
        "status_organizing": "Sedang memindahkan {count} file...",
        "status_organized": "✨ Berhasil merapikan {count} file!",
        "status_undoing": "Sedang mengembalikan file ke posisi awal...",
        "status_undone": "↩️ Berhasil mengembalikan {count} file ke posisi semula!",
        "empty_folder": "✨ Folder ini sudah bersih dan rapi! Tidak ada file yang perlu dipindahkan.",
        "no_filter_match": "Tidak ada file yang cocok dengan filter pencarian / kategori.",
        "dialog_confirm_title": "Konfirmasi Pemindahan",
        "dialog_confirm_msg": "Apakah Anda yakin ingin merapikan {count} file ini ke folder kategorinya masing-masing?\n\n(Tindakan ini aman dan bisa dibatalkan kapan saja dengan tombol Undo).",
        "dialog_success_title": "Selesai!",
        "dialog_success_msg": "✨ Berhasil merapikan {count} file!\n\nJika ada yang ingin dikembalikan, Anda dapat mengklik tombol 'Undo Terakhir' di pojok kanan atas.",
        "dialog_undo_confirm_title": "Konfirmasi Batalkan (Undo)",
        "dialog_undo_confirm_msg": "Apakah Anda ingin mengembalikan {count} file yang dirapikan pada {time} ke posisi aslinya?",
        "dialog_undo_success_title": "Undo Berhasil",
        "dialog_undo_success_msg": "Berhasil mengembalikan {count} file ke lokasi asalnya!",
        "dialog_no_undo_title": "Undo",
        "dialog_no_undo_msg": "Tidak ada riwayat pemindahan yang dapat dibatalkan.",
        "dialog_no_files_title": "Tidak Ada File",
        "dialog_no_files_msg": "Tidak ada file yang dipilih untuk dirapikan.",
        "dialog_invalid_dir_title": "Folder Tidak Valid",
        "dialog_invalid_dir_msg": "Folder path tidak ditemukan:\n{folder}",
        "rules_modal_title": "Aturan Kategori File",
        "rules_modal_header": "⚙️ Aturan & Kata Kunci Kategori",
        "rules_modal_desc": "File dengan kata kunci di bawah akan otomatis dimasukkan ke folder kategorinya.",
        "rules_modal_add_title": "Tambah Kata Kunci Baru:",
        "rules_modal_add_placeholder": "Kata kunci baru (misal: kalkulus, alpro, unity)",
        "rules_modal_add_btn": "Tambah",
        "rules_modal_save_btn": "Simpan & Tutup",
        "preset_project": "Folder Proyek",
        "preset_docs": "Dokumen",
        "custom_folder_btn": "📂 Pindahkan ke Folder Baru",
        "custom_folder_dialog_title": "Buat Folder & Pindahkan File",
        "custom_folder_dialog_header": "📂 Pindahkan {count} file terpilih ke folder baru",
        "custom_folder_dialog_label": "Nama Folder Baru:",
        "custom_folder_dialog_placeholder": "Ketik nama folder (misal: Tugas Kalkulus, Foto Liburan)",
        "custom_folder_dialog_create": "📂 Buat & Pindahkan",
        "custom_folder_dialog_cancel": "Batal",
        "custom_folder_empty_name": "Nama folder tidak boleh kosong.",
        "custom_folder_success_title": "Berhasil!",
        "custom_folder_success_msg": "✨ Berhasil memindahkan {count} file ke folder:\n📁 {folder}\n\nAnda bisa membatalkan dengan tombol Undo kapan saja.",
        "status_custom_moving": "Memindahkan {count} file ke folder '{folder}'...",
        "status_custom_done": "✨ {count} file berhasil dipindahkan ke folder '{folder}'!",
        "ctx_move_custom": "📂 Pindahkan {count} File ke Folder Baru...",
        "ctx_toggle_select": "☑/☐ Pilih / Batal Pilih File Ini",
        "cat_names": {
            "Kuliah": "Kuliah",
            "Coding": "Coding",
            "Games": "Games",
            "Documents": "Dokumen",
            "Archives": "Arsip",
            "Images": "Gambar",
            "Videos": "Video",
            "Audio": "Audio",
            "Installers": "Installer",
            "Design_3D": "Desain 3D",
            "Fonts": "Font",
            "Torrents": "Torrents",
            "Folders": "Folder",
            "Others": "Lainnya"
        }
    },
    "EN": {
        "window_title": "KQ Sortify - Intelligent File Organizer",
        "subtitle": "AUTOMATIC FILE ORGANIZER (COLLEGE • CODING • GAMES • DOCUMENTS)",
        "rules_btn": "⚙️ Category Rules",
        "undo_btn": "↩️ Undo Last Sort",
        "undo_count": "↩️ Undo ({count} Files)",
        "path_title": "📁 SOURCE FOLDER PATH TO ORGANIZE",
        "path_placeholder": "Type or paste folder path here (e.g. C:\\Users\\...\\Downloads)",
        "browse_btn": "📂 Browse Folder...",
        "scan_btn": "🔍 Scan Files",
        "scanning": "Scanning...",
        "mode_in_place": "Organize in-place (Create subfolders for College, Coding, Games, etc.)",
        "mode_subfolder": "Move to subfolder '/Organized/'",
        "stat_total_files": "TOTAL FILES",
        "stat_total_size": "TOTAL SIZE",
        "stat_categories": "CATEGORIES DETECTED",
        "stat_selected": "SELECTED FILES",
        "all_files": "All Files",
        "select_all": "Select All",
        "search_placeholder": "🔍 Search file name / extension...",
        "dry_run_badge": "🛡️ Safe Mode (Dry-Run Active)",
        "organize_btn": "⚡ Organize Now ({count} Files)",
        "organizing": "Organizing...",
        "col_select": "Select",
        "col_name": "File Name",
        "col_cat": "Category",
        "col_dest": "Target Folder",
        "col_size": "Size",
        "col_date": "Date Modified",
        "status_ready": "Ready. Enter or choose a folder path above to start organizing.",
        "status_scanning": "Scanning folder contents: {folder} ...",
        "status_scan_done": "Scan complete: {count} files found ({size}).",
        "status_organizing": "Moving {count} files...",
        "status_organized": "✨ Successfully organized {count} files!",
        "status_undoing": "Restoring files to original locations...",
        "status_undone": "↩️ Successfully restored {count} files to original locations!",
        "empty_folder": "✨ This folder is already clean and organized! No files need moving.",
        "no_filter_match": "No files match the search / category filter.",
        "dialog_confirm_title": "Confirm Organization",
        "dialog_confirm_msg": "Are you sure you want to organize these {count} files into their respective category folders?\n\n(This action is safe and can be undone anytime with the Undo button).",
        "dialog_success_title": "Done!",
        "dialog_success_msg": "✨ Successfully organized {count} files!\n\nIf you want to revert any changes, click 'Undo Last Sort' in the top right corner.",
        "dialog_undo_confirm_title": "Confirm Undo",
        "dialog_undo_confirm_msg": "Do you want to restore {count} files organized on {time} back to their original locations?",
        "dialog_undo_success_title": "Undo Successful",
        "dialog_undo_success_msg": "Successfully restored {count} files to their original locations!",
        "dialog_no_undo_title": "Undo",
        "dialog_no_undo_msg": "No organization history available to undo.",
        "dialog_no_files_title": "No Files Selected",
        "dialog_no_files_msg": "No files are selected to organize.",
        "dialog_invalid_dir_title": "Invalid Folder",
        "dialog_invalid_dir_msg": "Folder path not found:\n{folder}",
        "rules_modal_title": "File Category Rules",
        "rules_modal_header": "⚙️ Rules & Category Keywords",
        "rules_modal_desc": "Files matching keywords below will be automatically sorted into their category folder.",
        "rules_modal_add_title": "Add New Keyword:",
        "rules_modal_add_placeholder": "New keyword (e.g. homework, algorithm, unity)",
        "rules_modal_add_btn": "Add",
        "rules_modal_save_btn": "Save & Close",
        "preset_project": "Project Folder",
        "preset_docs": "Documents",
        "custom_folder_btn": "📂 Move to New Folder",
        "custom_folder_dialog_title": "Create Folder & Move Files",
        "custom_folder_dialog_header": "📂 Move {count} selected files to a new folder",
        "custom_folder_dialog_label": "New Folder Name:",
        "custom_folder_dialog_placeholder": "Type folder name (e.g. Vacation Photos, Project Alpha)",
        "custom_folder_dialog_create": "📂 Create & Move",
        "custom_folder_dialog_cancel": "Cancel",
        "custom_folder_empty_name": "Folder name cannot be empty.",
        "custom_folder_success_title": "Success!",
        "custom_folder_success_msg": "✨ Successfully moved {count} files to folder:\n📁 {folder}\n\nYou can undo this anytime with the Undo button.",
        "status_custom_moving": "Moving {count} files to folder '{folder}'...",
        "status_custom_done": "✨ {count} files successfully moved to folder '{folder}'!",
        "ctx_move_custom": "📂 Move {count} Files to New Folder...",
        "ctx_toggle_select": "☑/☐ Toggle Selection for This File",
        "cat_names": {
            "Kuliah": "College / Study",
            "Coding": "Coding",
            "Games": "Games",
            "Documents": "Documents",
            "Archives": "Archives",
            "Images": "Images",
            "Videos": "Videos",
            "Audio": "Audio",
            "Installers": "Installers",
            "Design_3D": "3D Design",
            "Fonts": "Fonts",
            "Torrents": "Torrents",
            "Folders": "Folders",
            "Others": "Others"
        }
    }
}

class KQSortifyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.rules = sorter_engine.load_rules()
        self.current_lang = self.rules.get("language", "ID")

        self.title(self.t("window_title"))
        self.geometry("1180x820")
        self.minsize(980, 680)

        # Set window icon
        ico_path = get_resource_path("logo.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # Center window on screen
        self.update_idletasks()
        width = 1180
        height = 820
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Data State
        self.current_scan_data = None
        self.active_category_filter = "ALL"
        self.search_filter_text = ""
        self._is_scanning = False
        self._is_organizing = False
        self._spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_idx = 0

        # Paths
        self.home_dir = str(Path.home())
        self.downloads_dir = str(Path.home() / "Downloads")
        self.desktop_dir = str(Path.home() / "Desktop")
        self.documents_dir = str(Path.home() / "Documents")

        self.create_ui()
        self.refresh_undo_button()

        # Auto scan default folder
        self.after(300, self.trigger_scan)

    def t(self, key, **kwargs):
        lang_dict = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["ID"])
        text = lang_dict.get(key, "")
        if not text:
            text = TRANSLATIONS["EN"].get(key, key)
        if kwargs and isinstance(text, str):
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def get_cat_name(self, cat_key):
        cat_map = self.t("cat_names")
        if isinstance(cat_map, dict):
            return cat_map.get(cat_key, cat_key)
        return cat_key

    def create_ui(self):
        # Main layout container
        self.main_container = ctk.CTkFrame(self, fg_color="#121214", corner_radius=0)
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)

        # Top Navigation Bar
        self.create_header()

        # Content Frame
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=24, pady=(12, 16))

        # Card 1: Folder Path Control
        self.create_path_card()

        # Card 2: Stats Dashboard
        self.create_stats_row()

        # Card 3: Category Filter Chips
        self.create_category_bar()

        # Card 4: Preview Table & Action Controls
        self.create_preview_section()

        # Bottom Status Bar
        self.create_status_bar()

    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_container, fg_color="#18181b", height=90, corner_radius=0)
        header_frame.pack(fill="x", side="top", padx=0, pady=0)
        header_frame.pack_propagate(False)

        inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=8)

        # Brand / Logo
        brand_frame = ctk.CTkFrame(inner, fg_color="transparent")
        brand_frame.pack(side="left", fill="y")

        png_path = get_resource_path("logo.png")
        if os.path.exists(png_path):
            try:
                pil_img = Image.open(png_path)
                self.logo_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(82, 70))
                logo_widget = ctk.CTkLabel(brand_frame, text="", image=self.logo_image)
                logo_widget.pack(side="left", padx=(0, 16))
            except Exception:
                logo_badge = ctk.CTkLabel(
                    brand_frame, text="KQ", font=ctk.CTkFont(size=24, weight="bold"),
                    text_color="#ffffff", fg_color="#3b82f6", corner_radius=12,
                    width=70, height=60
                )
                logo_badge.pack(side="left", padx=(0, 16))
        else:
            logo_badge = ctk.CTkLabel(
                brand_frame, text="KQ", font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#ffffff", fg_color="#3b82f6", corner_radius=12,
                width=70, height=60
            )
            logo_badge.pack(side="left", padx=(0, 16))

        title_box = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_box.pack(side="left")

        title_lbl = ctk.CTkLabel(
            title_box, text="KQ Sortify",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#f4f4f5"
        )
        title_lbl.pack(anchor="w")

        self.sub_lbl = ctk.CTkLabel(
            title_box, text=self.t("subtitle"),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#60a5fa"
        )
        self.sub_lbl.pack(anchor="w")

        # Top Right Actions
        actions_frame = ctk.CTkFrame(inner, fg_color="transparent")
        actions_frame.pack(side="right")

        # Language Switcher
        self.lang_switch = ctk.CTkSegmentedButton(
            actions_frame,
            values=["🇮🇩 ID", "🌐 EN"],
            command=self.on_lang_switch_clicked,
            width=115, height=34, corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            selected_color="#2563eb", selected_hover_color="#1d4ed8",
            unselected_color="#27272a", unselected_hover_color="#3f3f46"
        )
        self.lang_switch.set("🇮🇩 ID" if self.current_lang == "ID" else "🌐 EN")
        self.lang_switch.pack(side="right", padx=(10, 0))

        try:
            for b in self.lang_switch._buttons_dict.values():
                b.configure(cursor="hand2")
        except Exception:
            pass

        self.rules_btn = AnimatedCTkButton(
            actions_frame, text=self.t("rules_btn"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#27272a", hover_color="#38383f", text_color="#f4f4f5",
            border_width=1, border_color="#3f3f46", hover_border_color="#38bdf8",
            corner_radius=10, height=36,
            command=self.open_rules_dialog
        )
        self.rules_btn.pack(side="right", padx=(8, 0))

        self.undo_btn = AnimatedCTkButton(
            actions_frame, text=self.t("undo_btn"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#27272a", hover_color="#38383f", text_color="#f4f4f5",
            border_width=1, border_color="#3f3f46", hover_border_color="#fbbf24",
            corner_radius=10, height=36,
            state="disabled",
            command=self.trigger_undo
        )
        self.undo_btn.pack(side="right", padx=0)

    def on_lang_switch_clicked(self, value):
        new_lang = "EN" if "EN" in value else "ID"
        if new_lang != self.current_lang:
            self.set_language(new_lang)

    def set_language(self, lang):
        self.current_lang = lang
        self.rules["language"] = lang
        sorter_engine.save_rules(self.rules)
        self.update_language_ui()

    def update_language_ui(self):
        self.title(self.t("window_title"))
        self.sub_lbl.configure(text=self.t("subtitle"))
        self.rules_btn.configure(text=self.t("rules_btn"))
        self.refresh_undo_button()

        # Path card
        self.lbl_path_title.configure(text=self.t("path_title"))
        self.browse_btn.configure(text=self.t("browse_btn"))
        self.scan_btn.configure(text=self.t("scan_btn"))
        self.mode1.configure(text=self.t("mode_in_place"))
        self.mode2.configure(text=self.t("mode_subfolder"))
        self.btn_preset_docs.configure(text=self.t("preset_docs"))
        self.btn_preset_project.configure(text=self.t("preset_project"))

        # Stats
        self.stat_titles["total_files"].configure(text=self.t("stat_total_files"))
        self.stat_titles["total_size"].configure(text=self.t("stat_total_size"))
        self.stat_titles["categories"].configure(text=self.t("stat_categories"))
        self.stat_titles["selected_count"].configure(text=self.t("stat_selected"))

        # Toolbar
        self.select_all_cb.configure(text=self.t("select_all"))
        self.search_entry.configure(placeholder_text=self.t("search_placeholder"))
        self.dry_run_badge.configure(text=self.t("dry_run_badge"))
        self.custom_folder_btn.configure(text=self.t("custom_folder_btn"))

        # Treeview Headings
        self.tree.heading("#0", text=self.t("col_select"))
        self.tree.heading("name", text=self.t("col_name"))
        self.tree.heading("cat", text=self.t("col_cat"))
        self.tree.heading("dest", text=self.t("col_dest"))
        self.tree.heading("size", text=self.t("col_size"))
        self.tree.heading("date", text=self.t("col_date"))

        # Category pills and rows
        if self.current_scan_data:
            self.render_category_pills(self.current_scan_data.get("category_counts", {}))
            self.render_file_rows()
        else:
            self.render_category_pills({})

        self.update_selected_count()
        self.status_lbl.configure(text=self.t("status_ready"))

    def create_path_card(self):
        card = ctk.CTkFrame(self.content_frame, fg_color="#18181b", corner_radius=14, border_width=1, border_color="#27272a")
        card.pack(fill="x", pady=(0, 12), padx=0)
        attach_card_hover(card, normal_bg="#18181b", hover_bg="#1c1c20", normal_border="#27272a", hover_border="#3f3f46")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)

        # Header of Path Card
        header_row = ctk.CTkFrame(inner, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 10))

        self.lbl_path_title = ctk.CTkLabel(
            header_row, text=self.t("path_title"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#ff8474"
        )
        self.lbl_path_title.pack(side="left")

        # Preset Buttons
        preset_frame = ctk.CTkFrame(header_row, fg_color="transparent")
        preset_frame.pack(side="right")

        self.btn_preset_down = AnimatedCTkButton(
            preset_frame, text="Downloads", font=ctk.CTkFont(size=11),
            fg_color="#27272a", hover_color="#38383f", text_color="#d4d4d8",
            border_width=1, border_color="#3f3f46", hover_border_color="#60a5fa",
            height=26, corner_radius=14, command=lambda: self.select_preset(self.downloads_dir)
        )
        self.btn_preset_down.pack(side="left", padx=4)

        self.btn_preset_desk = AnimatedCTkButton(
            preset_frame, text="Desktop", font=ctk.CTkFont(size=11),
            fg_color="#27272a", hover_color="#38383f", text_color="#d4d4d8",
            border_width=1, border_color="#3f3f46", hover_border_color="#60a5fa",
            height=26, corner_radius=14, command=lambda: self.select_preset(self.desktop_dir)
        )
        self.btn_preset_desk.pack(side="left", padx=4)

        self.btn_preset_docs = AnimatedCTkButton(
            preset_frame, text=self.t("preset_docs"), font=ctk.CTkFont(size=11),
            fg_color="#27272a", hover_color="#38383f", text_color="#d4d4d8",
            border_width=1, border_color="#3f3f46", hover_border_color="#60a5fa",
            height=26, corner_radius=14, command=lambda: self.select_preset(self.documents_dir)
        )
        self.btn_preset_docs.pack(side="left", padx=4)

        self.btn_preset_project = AnimatedCTkButton(
            preset_frame, text=self.t("preset_project"), font=ctk.CTkFont(size=11),
            fg_color="#27272a", hover_color="#38383f", text_color="#d4d4d8",
            border_width=1, border_color="#3f3f46", hover_border_color="#60a5fa",
            height=26, corner_radius=14, command=lambda: self.select_preset(os.path.dirname(os.path.abspath(__file__)))
        )
        self.btn_preset_project.pack(side="left", padx=4)

        # Path Entry Row
        input_row = ctk.CTkFrame(inner, fg_color="transparent")
        input_row.pack(fill="x", pady=(0, 10))

        initial_path = self.downloads_dir if os.path.exists(self.downloads_dir) else self.home_dir
        self.path_entry = ctk.CTkEntry(
            input_row,
            placeholder_text=self.t("path_placeholder"),
            font=ctk.CTkFont(size=13),
            fg_color="#09090b", border_color="#3f3f46", text_color="#f4f4f5",
            corner_radius=10, height=42
        )
        self.path_entry.insert(0, initial_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.path_entry.bind("<Return>", lambda event: self.trigger_scan())
        attach_entry_glow(self.path_entry, normal_border="#3f3f46", focus_border="#3b82f6")

        self.browse_btn = AnimatedCTkButton(
            input_row, text=self.t("browse_btn"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#27272a", hover_color="#38383f", text_color="#f4f4f5",
            border_width=1, border_color="#3f3f46", hover_border_color="#60a5fa",
            corner_radius=10, height=42, width=130,
            command=self.browse_directory
        )
        self.browse_btn.pack(side="left", padx=(0, 10))

        self.scan_btn = AnimatedCTkButton(
            input_row, text=self.t("scan_btn"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563eb", hover_color="#3b82f6", text_color="#ffffff",
            border_width=1, border_color="#1d4ed8", hover_border_color="#60a5fa",
            corner_radius=10, height=42, width=130,
            command=self.trigger_scan
        )
        self.scan_btn.pack(side="left")

        # Organization Options Row
        options_row = ctk.CTkFrame(inner, fg_color="transparent")
        options_row.pack(fill="x")

        self.target_mode_var = ctk.StringVar(value="in_place")

        self.mode1 = ctk.CTkRadioButton(
            options_row, text=self.t("mode_in_place"),
            variable=self.target_mode_var, value="in_place",
            font=ctk.CTkFont(size=12), text_color="#a1a1aa",
            fg_color="#3b82f6", hover_color="#2563eb"
        )
        self.mode1.pack(side="left", padx=(0, 24))

        self.mode2 = ctk.CTkRadioButton(
            options_row, text=self.t("mode_subfolder"),
            variable=self.target_mode_var, value="subfolder",
            font=ctk.CTkFont(size=12), text_color="#a1a1aa",
            fg_color="#3b82f6", hover_color="#2563eb"
        )
        self.mode2.pack(side="left")

        try:
            self.mode1.configure(cursor="hand2")
            self.mode2.configure(cursor="hand2")
        except Exception:
            pass

    def create_stats_row(self):
        stats_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 12))

        self.stat_cards = {}
        self.stat_titles = {}
        items = [
            ("total_files", "stat_total_files", "0", "#60a5fa"),
            ("total_size", "stat_total_size", "0 B", "#34d399"),
            ("categories", "stat_categories", "0", "#a78bfa"),
            ("selected_count", "stat_selected", "0", "#ff8474")
        ]

        for i, (key, title_key, default_val, color) in enumerate(items):
            card = ctk.CTkFrame(stats_frame, fg_color="#18181b", corner_radius=12, border_width=1, border_color="#27272a")
            card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 8, 0))
            attach_card_hover(card, normal_bg="#18181b", hover_bg="#202024", normal_border="#27272a", hover_border=color)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=14, pady=10)

            val_lbl = ctk.CTkLabel(
                inner, text=default_val,
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color=color
            )
            val_lbl.pack(anchor="w")

            title_lbl = ctk.CTkLabel(
                inner, text=self.t(title_key),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#71717a"
            )
            title_lbl.pack(anchor="w")

            self.stat_cards[key] = val_lbl
            self.stat_titles[key] = title_lbl

    def create_category_bar(self):
        self.cat_bar_card = ctk.CTkFrame(self.content_frame, fg_color="#18181b", corner_radius=12, border_width=1, border_color="#27272a")
        self.cat_bar_card.pack(fill="x", pady=(0, 12))

        self.cat_bar_scroll = ctk.CTkScrollableFrame(self.cat_bar_card, orientation="horizontal", height=42, fg_color="transparent")
        self.cat_bar_scroll.pack(fill="x", padx=10, pady=6)

        self.cat_buttons = {}
        self.render_category_pills({})

    def render_category_pills(self, counts):
        for widget in self.cat_bar_scroll.winfo_children():
            widget.destroy()
        self.cat_buttons = {}

        total_files = sum(counts.values()) if counts else 0
        all_text = f"{self.t('all_files')} ({total_files})"
        all_btn = AnimatedCTkButton(
            self.cat_bar_scroll,
            text=all_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#3f3f46" if self.active_category_filter == "ALL" else "#27272a",
            hover_color="#52525b",
            border_color="#52525b" if self.active_category_filter == "ALL" else "#27272a",
            hover_border_color="#a1a1aa",
            border_width=1,
            text_color="#ffffff",
            height=30, corner_radius=15,
            command=lambda: self.set_category_filter("ALL")
        )
        all_btn.pack(side="left", padx=4)
        self.cat_buttons["ALL"] = all_btn

        for cat, cnt in counts.items():
            icon = CATEGORY_ICONS.get(cat, "📁")
            color = CATEGORY_COLORS.get(cat, "#38bdf8")
            is_active = (self.active_category_filter == cat)
            display_name = self.get_cat_name(cat)

            btn = AnimatedCTkButton(
                self.cat_bar_scroll,
                text=f"{icon} {display_name} ({cnt})",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=color if is_active else "#27272a",
                hover_color=color if is_active else "#333338",
                border_color=color if is_active else "#27272a",
                hover_border_color=color,
                border_width=1,
                text_color="#000000" if is_active else "#f4f4f5",
                height=30, corner_radius=15,
                command=lambda c=cat: self.set_category_filter(c)
            )
            btn.pack(side="left", padx=4)
            self.cat_buttons[cat] = btn

    def set_category_filter(self, category):
        self.active_category_filter = category
        if self.current_scan_data:
            self.render_category_pills(self.current_scan_data.get("category_counts", {}))
            self.render_file_rows()

    def create_preview_section(self):
        self.preview_card = ctk.CTkFrame(self.content_frame, fg_color="#18181b", corner_radius=14, border_width=1, border_color="#27272a")
        self.preview_card.pack(fill="both", expand=True, pady=(0, 6))

        # Preview Toolbar
        toolbar = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        toolbar.pack(fill="x", padx=16, pady=12)

        # Select All Checkbox
        self.select_all_var = ctk.BooleanVar(value=True)
        self.select_all_cb = ctk.CTkCheckBox(
            toolbar, text=self.t("select_all"),
            variable=self.select_all_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3b82f6", hover_color="#2563eb",
            command=self.toggle_select_all
        )
        self.select_all_cb.pack(side="left", padx=(0, 16))
        try:
            self.select_all_cb.configure(cursor="hand2")
        except Exception:
            pass

        # Search / Filter Entry
        self.search_entry = ctk.CTkEntry(
            toolbar, placeholder_text=self.t("search_placeholder"),
            font=ctk.CTkFont(size=12),
            fg_color="#09090b", border_color="#3f3f46", text_color="#f4f4f5",
            width=260, height=34, corner_radius=8
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        attach_entry_glow(self.search_entry, normal_border="#3f3f46", focus_border="#38bdf8")

        # Primary Action Button: Organize
        self.organize_btn = AnimatedCTkButton(
            toolbar, text=self.t("organize_btn", count=0),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#ff8474", hover_color="#ffa090", text_color="#18181b",
            border_width=1, border_color="#e11d48", hover_border_color="#ffffff",
            corner_radius=10, height=36,
            state="disabled",
            command=self.trigger_organize
        )
        self.organize_btn.pack(side="right")

        # Custom Folder Button: Move selected files to a user-named folder
        self.custom_folder_btn = AnimatedCTkButton(
            toolbar, text=self.t("custom_folder_btn"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#27272a", hover_color="#38383f", text_color="#f4f4f5",
            border_width=1, border_color="#3f3f46", hover_border_color="#a78bfa",
            corner_radius=10, height=36,
            state="disabled",
            command=self.open_custom_folder_dialog
        )
        self.custom_folder_btn.pack(side="right", padx=(0, 10))

        # Dry-run badge
        self.dry_run_badge = ctk.CTkLabel(
            toolbar, text=self.t("dry_run_badge"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#34d399", fg_color="#064e3b", corner_radius=8,
            padx=10, pady=4
        )
        self.dry_run_badge.pack(side="right", padx=(0, 14))

        # Treeview styling with sleek dark theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
            background="#141416",
            foreground="#f4f4f5",
            fieldbackground="#141416",
            rowheight=34,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        style.configure("Dark.Treeview.Heading",
            background="#0c0c0e",
            foreground="#a1a1aa",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=(6, 8)
        )
        style.map("Dark.Treeview",
            background=[("selected", "#27272a")],
            foreground=[("selected", "#ffffff")]
        )

        table_container = ctk.CTkFrame(self.preview_card, fg_color="#141416", corner_radius=8)
        table_container.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.tree = ttk.Treeview(
            table_container, style="Dark.Treeview",
            columns=("name", "cat", "dest", "size", "date"),
            show="tree headings", selectmode="browse"
        )
        self.tree.heading("#0", text=self.t("col_select"), anchor="center")
        self.tree.column("#0", width=55, minwidth=50, stretch=False, anchor="center")

        self.tree.heading("name", text=self.t("col_name"), anchor="w")
        self.tree.column("name", width=380, minwidth=220, stretch=True, anchor="w")

        self.tree.heading("cat", text=self.t("col_cat"), anchor="w")
        self.tree.column("cat", width=150, minwidth=120, stretch=False, anchor="w")

        self.tree.heading("dest", text=self.t("col_dest"), anchor="w")
        self.tree.column("dest", width=220, minwidth=140, stretch=False, anchor="w")

        self.tree.heading("size", text=self.t("col_size"), anchor="e")
        self.tree.column("size", width=95, minwidth=80, stretch=False, anchor="e")

        self.tree.heading("date", text=self.t("col_date"), anchor="e")
        self.tree.column("date", width=110, minwidth=90, stretch=False, anchor="e")

        for cat_name, color in CATEGORY_COLORS.items():
            self.tree.tag_configure(cat_name, foreground=color)

        # Hover row style
        self.tree.tag_configure("hover_row", background="#202026")
        self._last_hovered_row = None

        def on_tree_motion(event):
            row_id = self.tree.identify_row(event.y)
            if row_id != self._last_hovered_row:
                if self._last_hovered_row and self.tree.exists(self._last_hovered_row):
                    tags = [t for t in self.tree.item(self._last_hovered_row, "tags") if t != "hover_row"]
                    self.tree.item(self._last_hovered_row, tags=tags)
                if row_id and self.tree.exists(row_id):
                    tags = list(self.tree.item(row_id, "tags"))
                    if "hover_row" not in tags:
                        tags.append("hover_row")
                        self.tree.item(row_id, tags=tags)
                self._last_hovered_row = row_id

        def on_tree_leave(event):
            if self._last_hovered_row and self.tree.exists(self._last_hovered_row):
                tags = [t for t in self.tree.item(self._last_hovered_row, "tags") if t != "hover_row"]
                self.tree.item(self._last_hovered_row, tags=tags)
            self._last_hovered_row = None

        self.tree.bind("<Motion>", on_tree_motion)
        self.tree.bind("<Leave>", on_tree_leave)

        self.scrollbar = ctk.CTkScrollbar(table_container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.tree.bind("<Button-3>", self.on_tree_right_click)
        self.tree.bind("<Button-2>", self.on_tree_right_click)
        self.tree.bind("<space>", self.on_tree_space)

    def create_status_bar(self):
        status_bar = ctk.CTkFrame(self.main_container, fg_color="#09090b", height=28, corner_radius=0)
        status_bar.pack(fill="x", side="bottom")

        self.status_lbl = ctk.CTkLabel(
            status_bar, text=self.t("status_ready"),
            font=ctk.CTkFont(size=11), text_color="#a1a1aa"
        )
        self.status_lbl.pack(side="left", padx=16)

    def select_preset(self, path):
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, path)
        self.trigger_scan()

    def browse_directory(self):
        initial = self.path_entry.get().strip()
        if not os.path.isdir(initial):
            initial = self.downloads_dir
        selected = filedialog.askdirectory(initialdir=initial, title=self.t("browse_btn"))
        if selected:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, selected)
            self.trigger_scan()

    def _update_scan_spinner(self):
        if getattr(self, "_is_scanning", False):
            frame = self._spinner_frames[self._spinner_idx % len(self._spinner_frames)]
            self._spinner_idx += 1
            self.scan_btn.configure(text=f"{frame} {self.t('scanning')}")
            self.after(80, self._update_scan_spinner)

    def trigger_scan(self):
        folder = self.path_entry.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning(self.t("dialog_invalid_dir_title"), self.t("dialog_invalid_dir_msg", folder=folder))
            return

        self._is_scanning = True
        self._spinner_idx = 0
        self.scan_btn.configure(state="disabled")
        self._update_scan_spinner()
        self.status_lbl.configure(text=self.t("status_scanning", folder=folder))

        def run():
            try:
                target_mode = self.target_mode_var.get()
                rules = sorter_engine.load_rules()
                res = sorter_engine.scan_directory(folder, target_mode=target_mode, rules=rules)
                self.after(0, lambda: self.on_scan_success(res))
            except Exception as e:
                self.after(0, lambda: self.on_scan_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def on_scan_success(self, scan_data):
        self._is_scanning = False
        self.scan_btn.configure(state="normal", text=self.t("scan_btn"))
        self.current_scan_data = scan_data

        # Update stats
        self.stat_cards["total_files"].configure(text=str(scan_data["total_files"]))
        self.stat_cards["total_size"].configure(text=scan_data["total_size_formatted"])
        self.stat_cards["categories"].configure(text=str(len(scan_data["category_counts"])))

        # Update category pills
        self.render_category_pills(scan_data["category_counts"])

        # Render rows
        self.render_file_rows()
        self.status_lbl.configure(text=self.t("status_scan_done", count=scan_data['total_files'], size=scan_data['total_size_formatted']))

    def on_scan_error(self, err_msg):
        self._is_scanning = False
        self.scan_btn.configure(state="normal", text=self.t("scan_btn"))
        self.status_lbl.configure(text=f"Error: {err_msg}")
        messagebox.showerror(self.t("dialog_invalid_dir_title"), f"Error:\n{err_msg}")

    def on_search_change(self, event=None):
        self.search_filter_text = self.search_entry.get().lower().strip()
        self.render_file_rows()

    def render_file_rows(self):
        self.tree.delete(*self.tree.get_children())
        self._last_hovered_row = None
        self._last_clicked_id = None

        if not self.current_scan_data or not self.current_scan_data.get("items"):
            self.update_selected_count()
            return

        query = self.search_filter_text
        cat_filter = self.active_category_filter

        for item in self.current_scan_data["items"]:
            if cat_filter != "ALL" and item["category"] != cat_filter:
                continue
            if query:
                if query not in item["name"].lower() and query not in item["extension"].lower():
                    continue

            chk = "☑" if item.get("selected", True) else "☐"
            cat_key = item["category"]
            cat_name = self.get_cat_name(cat_key)
            cat_icon = CATEGORY_ICONS.get(cat_key, "📁")
            target_folder = os.path.basename(item["target_dir"])
            date_str = item["modified_time"][:10]

            self.tree.insert(
                "", "end", iid=item["id"],
                text=chk,
                values=(
                    item["name"],
                    f"{cat_icon} {cat_name}",
                    f"➡️ /{target_folder}/",
                    item["size_formatted"],
                    date_str
                ),
                tags=(cat_key,)
            )

        self.update_selected_count()

    def toggle_item_selection(self, item_id):
        if not self.current_scan_data:
            return
        for it in self.current_scan_data.get("items", []):
            if it["id"] == item_id:
                it["selected"] = not it.get("selected", True)
                chk = "☑" if it["selected"] else "☐"
                try:
                    self.tree.item(item_id, text=chk)
                except Exception:
                    pass
                break
        self.update_selected_count()

    def select_range(self, start_id, end_id, target_state=True):
        children = list(self.tree.get_children())
        if start_id not in children or end_id not in children:
            return

        i1 = children.index(start_id)
        i2 = children.index(end_id)
        range_ids = set(children[min(i1, i2):max(i1, i2) + 1])

        item_map = {it["id"]: it for it in self.current_scan_data.get("items", [])}

        for item_id in range_ids:
            if item_id in item_map:
                item_map[item_id]["selected"] = target_state
                chk = "☑" if target_state else "☐"
                try:
                    self.tree.item(item_id, text=chk)
                except Exception:
                    pass

        try:
            self.tree.selection_set(tuple(range_ids))
        except Exception:
            pass

        self.update_selected_count()

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        is_shift = bool(event.state & 0x0001) or bool(event.state & 1)
        last_id = getattr(self, "_last_clicked_id", None)
        children = list(self.tree.get_children())

        if is_shift and last_id and last_id in children and last_id != item_id:
            self.select_range(last_id, item_id, target_state=True)
        else:
            self.toggle_item_selection(item_id)
            self._last_clicked_id = item_id

    def on_tree_space(self, event):
        selected = self.tree.selection()
        for item_id in selected:
            self.toggle_item_selection(item_id)

    def on_tree_right_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id and row_id not in self.tree.selection():
            self.tree.selection_set(row_id)

        items_selected = [it for it in self.current_scan_data.get("items", []) if it.get("selected", True)] if self.current_scan_data else []
        count = len(items_selected)

        import tkinter as tk
        menu = tk.Menu(self, tearoff=0, bg="#1c1c1e", fg="#f4f4f5", activebackground="#3b82f6", activeforeground="#ffffff", bd=1, relief="solid")

        menu.add_command(
            label=self.t("ctx_move_custom", count=count),
            command=self.open_custom_folder_dialog,
            state="normal" if count > 0 else "disabled"
        )
        menu.add_separator()
        if row_id:
            menu.add_command(
                label=self.t("ctx_toggle_select"),
                command=lambda: self.toggle_item_selection(row_id)
            )
        menu.add_command(
            label=self.t("select_all"),
            command=lambda: (self.select_all_var.set(True), self.toggle_select_all())
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def toggle_select_all(self):
        val = self.select_all_var.get()
        if self.current_scan_data:
            for it in self.current_scan_data.get("items", []):
                it["selected"] = val
            chk = "☑" if val else "☐"
            for child in self.tree.get_children():
                self.tree.item(child, text=chk)
        self.update_selected_count()

    def update_selected_count(self):
        if not self.current_scan_data:
            count = 0
        else:
            count = sum(1 for it in self.current_scan_data.get("items", []) if it.get("selected", True))

        self.stat_cards["selected_count"].configure(text=str(count))
        self.organize_btn.configure(
            text=self.t("organize_btn", count=count),
            state="normal" if count > 0 else "disabled"
        )
        self.custom_folder_btn.configure(
            state="normal" if count > 0 else "disabled"
        )

    def _update_organize_spinner(self):
        if getattr(self, "_is_organizing", False):
            frame = self._spinner_frames[self._spinner_idx % len(self._spinner_frames)]
            self._spinner_idx += 1
            self.organize_btn.configure(text=f"⚡ {frame} {self.t('organizing')}")
            self.after(80, self._update_organize_spinner)

    def open_custom_folder_dialog(self):
        """Open a modal dialog asking for a folder name, then move selected files there."""
        if not self.current_scan_data:
            return

        items_to_move = [it for it in self.current_scan_data.get("items", []) if it.get("selected", True)]
        if not items_to_move:
            messagebox.showinfo(self.t("dialog_no_files_title"), self.t("dialog_no_files_msg"))
            return

        count = len(items_to_move)

        dialog = ctk.CTkToplevel(self)
        dialog.title(self.t("custom_folder_dialog_title"))
        dialog.geometry("520x260")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color="#121214")

        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 260
        y = self.winfo_y() + (self.winfo_height() // 2) - 130
        dialog.geometry(f"+{x}+{y}")

        # Try to set icon
        ico_path = get_resource_path("logo.ico")
        if os.path.exists(ico_path):
            try:
                dialog.iconbitmap(ico_path)
            except Exception:
                pass

        # Header
        header_lbl = ctk.CTkLabel(
            dialog, text=self.t("custom_folder_dialog_header", count=count),
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#f4f4f5"
        )
        header_lbl.pack(pady=(24, 6))

        # Description showing selected file names preview
        file_names_preview = ", ".join([it["name"] for it in items_to_move[:3]])
        if count > 3:
            file_names_preview += f" ... (+{count - 3})"
        desc_lbl = ctk.CTkLabel(
            dialog, text=file_names_preview,
            font=ctk.CTkFont(size=10), text_color="#a1a1aa",
            wraplength=460
        )
        desc_lbl.pack(pady=(0, 14))

        # Folder name input
        input_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        input_frame.pack(fill="x", padx=30, pady=(0, 6))

        ctk.CTkLabel(
            input_frame, text=self.t("custom_folder_dialog_label"),
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#d4d4d8"
        ).pack(anchor="w", pady=(0, 4))

        folder_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text=self.t("custom_folder_dialog_placeholder"),
            font=ctk.CTkFont(size=13),
            fg_color="#09090b", border_color="#3f3f46", text_color="#f4f4f5",
            corner_radius=10, height=42
        )
        folder_entry.pack(fill="x")
        folder_entry.focus_set()
        attach_entry_glow(folder_entry, normal_border="#3f3f46", focus_border="#a78bfa")

        # Action buttons row
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(14, 20))

        def on_create():
            name = folder_entry.get().strip()
            if not name:
                messagebox.showwarning(
                    self.t("custom_folder_dialog_title"),
                    self.t("custom_folder_empty_name")
                )
                folder_entry.focus_set()
                return
            # Sanitize illegal chars for folder name
            illegal = '<>:"/\\|?*'
            for ch in illegal:
                name = name.replace(ch, '_')
            dialog.destroy()
            self.trigger_custom_move(items_to_move, name)

        folder_entry.bind("<Return>", lambda e: on_create())

        create_btn = AnimatedCTkButton(
            btn_frame, text=self.t("custom_folder_dialog_create"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#7c3aed", hover_color="#8b5cf6", text_color="#ffffff",
            border_width=1, border_color="#6d28d9", hover_border_color="#c4b5fd",
            corner_radius=10, height=40,
            command=on_create
        )
        create_btn.pack(side="right")

        cancel_btn = AnimatedCTkButton(
            btn_frame, text=self.t("custom_folder_dialog_cancel"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#27272a", hover_color="#38383f", text_color="#a1a1aa",
            border_width=1, border_color="#3f3f46", hover_border_color="#71717a",
            corner_radius=10, height=40,
            command=dialog.destroy
        )
        cancel_btn.pack(side="right", padx=(0, 10))

    def trigger_custom_move(self, items_to_move, folder_name):
        """Move selected files to a custom-named folder in the source directory."""
        source_folder = self.path_entry.get().strip()

        self.custom_folder_btn.configure(state="disabled")
        self.organize_btn.configure(state="disabled")
        self.status_lbl.configure(text=self.t("status_custom_moving", count=len(items_to_move), folder=folder_name))

        def run():
            try:
                res = sorter_engine.move_to_custom_folder(items_to_move, folder_name, source_folder)
                self.after(0, lambda: self.on_custom_move_complete(res))
            except Exception as e:
                self.after(0, lambda: self.on_custom_move_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def on_custom_move_complete(self, res):
        self.refresh_undo_button()
        moved = res.get("moved_count", 0)
        folder = res.get("folder_name", "")
        self.status_lbl.configure(text=self.t("status_custom_done", count=moved, folder=folder))
        messagebox.showinfo(
            self.t("custom_folder_success_title"),
            self.t("custom_folder_success_msg", count=moved, folder=folder)
        )
        self.trigger_scan()

    def on_custom_move_error(self, err_msg):
        self.status_lbl.configure(text=f"Error: {err_msg}")
        messagebox.showerror("Error", f"Error:\n{err_msg}")
        self.trigger_scan()

    def trigger_organize(self):
        if not self.current_scan_data:
            return

        items_to_move = [it for it in self.current_scan_data.get("items", []) if it.get("selected", True)]
        if not items_to_move:
            messagebox.showinfo(self.t("dialog_no_files_title"), self.t("dialog_no_files_msg"))
            return

        confirm = messagebox.askyesno(
            self.t("dialog_confirm_title"),
            self.t("dialog_confirm_msg", count=len(items_to_move))
        )
        if not confirm:
            return

        self._is_organizing = True
        self._spinner_idx = 0
        self.organize_btn.configure(state="disabled")
        self._update_organize_spinner()
        self.status_lbl.configure(text=self.t("status_organizing", count=len(items_to_move)))

        def run():
            try:
                res = sorter_engine.execute_organize(items_to_move)
                self.after(0, lambda: self.on_organize_complete(res))
            except Exception as e:
                self.after(0, lambda: self.on_organize_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def on_organize_complete(self, res):
        self._is_organizing = False
        self.refresh_undo_button()
        moved = res.get("moved_count", 0)
        self.status_lbl.configure(text=self.t("status_organized", count=moved))
        messagebox.showinfo(
            self.t("dialog_success_title"),
            self.t("dialog_success_msg", count=moved)
        )
        self.trigger_scan()

    def on_organize_error(self, err_msg):
        self._is_organizing = False
        self.status_lbl.configure(text=f"Error: {err_msg}")
        messagebox.showerror("Error", f"Error:\n{err_msg}")
        self.trigger_scan()

    def refresh_undo_button(self):
        last_undo = sorter_engine.get_last_undoable_batch()
        if last_undo and last_undo["moved_count"] > 0:
            self.undo_btn.configure(
                state="normal",
                text=self.t("undo_count", count=last_undo['moved_count']),
                fg_color="#e11d48", hover_color="#be123c",
                border_color="#f43f5e", hover_border_color="#fda4af"
            )
        else:
            self.undo_btn.configure(
                state="disabled",
                text=self.t("undo_btn"),
                fg_color="#27272a", hover_color="#38383f",
                border_color="#3f3f46", hover_border_color="#3f3f46"
            )

    def trigger_undo(self):
        last_undo = sorter_engine.get_last_undoable_batch()
        if not last_undo:
            messagebox.showinfo(self.t("dialog_no_undo_title"), self.t("dialog_no_undo_msg"))
            return

        confirm = messagebox.askyesno(
            self.t("dialog_undo_confirm_title"),
            self.t("dialog_undo_confirm_msg", count=last_undo['moved_count'], time=last_undo['timestamp'])
        )
        if not confirm:
            return

        self.undo_btn.configure(state="disabled", text=self.t("status_undoing"))
        self.status_lbl.configure(text=self.t("status_undoing"))

        def run():
            try:
                res = sorter_engine.undo_last_batch(last_undo["batch_id"])
                self.after(0, lambda: self.on_undo_complete(res))
            except Exception as e:
                self.after(0, lambda: self.on_undo_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def on_undo_complete(self, res):
        self.refresh_undo_button()
        reverted = res.get("reverted_count", 0)
        self.status_lbl.configure(text=self.t("status_undone", count=reverted))
        messagebox.showinfo(self.t("dialog_undo_success_title"), self.t("dialog_undo_success_msg", count=reverted))
        self.trigger_scan()

    def on_undo_error(self, err_msg):
        self.refresh_undo_button()
        self.status_lbl.configure(text=f"Error Undo: {err_msg}")
        messagebox.showerror("Error Undo", f"Error:\n{err_msg}")

    def open_rules_dialog(self):
        dialog = RulesEditorDialog(self, self.rules)
        self.wait_window(dialog)
        self.rules = sorter_engine.load_rules()
        self.trigger_scan()

class RulesEditorDialog(ctk.CTkToplevel):
    def __init__(self, parent, rules):
        super().__init__(parent)
        self.parent = parent
        self.title(self.parent.t("rules_modal_title"))
        self.geometry("660x570")
        self.rules = rules

        self.transient(parent)
        self.grab_set()

        # Center dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 330
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 285
        self.geometry(f"+{x}+{y}")

        self.create_ui()

    def create_ui(self):
        lbl = ctk.CTkLabel(
            self, text=self.parent.t("rules_modal_header"),
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#f4f4f5"
        )
        lbl.pack(pady=(16, 4))

        sub = ctk.CTkLabel(
            self, text=self.parent.t("rules_modal_desc"),
            font=ctk.CTkFont(size=11), text_color="#a1a1aa"
        )
        sub.pack(pady=(0, 12))

        # Scrollable list of categories
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#18181b", height=320)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.render_rules()

        # Add Keyword Section
        add_frame = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=10)
        add_frame.pack(fill="x", padx=20, pady=(0, 14))

        add_lbl = ctk.CTkLabel(
            add_frame, text=self.parent.t("rules_modal_add_title"),
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#f4f4f5"
        )
        add_lbl.pack(anchor="w", padx=12, pady=(8, 4))

        input_row = ctk.CTkFrame(add_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=12, pady=(0, 10))

        self.cat_select = ctk.CTkComboBox(
            input_row, values=["Kuliah", "Coding", "Games", "Documents"],
            width=130, font=ctk.CTkFont(size=12)
        )
        self.cat_select.pack(side="left", padx=(0, 8))

        self.kw_entry = ctk.CTkEntry(
            input_row, placeholder_text=self.parent.t("rules_modal_add_placeholder"),
            font=ctk.CTkFont(size=12)
        )
        self.kw_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        attach_entry_glow(self.kw_entry, normal_border="#3f3f46", focus_border="#38bdf8")

        add_btn = AnimatedCTkButton(
            input_row, text=self.parent.t("rules_modal_add_btn"), width=80,
            fg_color="#27272a", hover_color="#38383f",
            border_width=1, border_color="#3f3f46", hover_border_color="#38bdf8",
            command=self.add_keyword
        )
        add_btn.pack(side="left")

        # Bottom close
        close_btn = AnimatedCTkButton(
            self, text=self.parent.t("rules_modal_save_btn"),
            fg_color="#2563eb", hover_color="#3b82f6",
            border_width=1, border_color="#1d4ed8", hover_border_color="#60a5fa",
            command=self.save_and_close
        )
        close_btn.pack(pady=(0, 16))

    def render_rules(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        categories = self.rules.get("categories", {})
        for cat_name, info in categories.items():
            card = ctk.CTkFrame(self.scroll, fg_color="#27272a", corner_radius=8)
            card.pack(fill="x", pady=4, padx=4)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(6, 2))

            icon = CATEGORY_ICONS.get(cat_name, "📁")
            color = CATEGORY_COLORS.get(cat_name, "#38bdf8")
            display_cat = self.parent.get_cat_name(cat_name)

            ctk.CTkLabel(
                top, text=f"{icon} {display_cat} ({cat_name})",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=color
            ).pack(side="left")

            ctk.CTkLabel(
                top, text=f"Folder: /{info.get('folder_name', cat_name)}",
                font=ctk.CTkFont(size=10), text_color="#a1a1aa"
            ).pack(side="right")

            kws = info.get("keywords", [])
            kw_str = ", ".join(kws[:12]) if kws else "(Extensions only)"
            if len(kws) > 12:
                kw_str += f" (+{len(kws)-12} more)"

            ctk.CTkLabel(
                card, text=f"Keywords: {kw_str}",
                font=ctk.CTkFont(size=10), text_color="#d4d4d8",
                anchor="w", wraplength=540, justify="left"
            ).pack(fill="x", padx=10, pady=(0, 6))

    def add_keyword(self):
        cat = self.cat_select.get()
        kw = self.kw_entry.get().strip().lower()
        if not kw:
            return

        if cat in self.rules["categories"]:
            if "keywords" not in self.rules["categories"][cat]:
                self.rules["categories"][cat]["keywords"] = []
            if kw not in self.rules["categories"][cat]["keywords"]:
                self.rules["categories"][cat]["keywords"].append(kw)
                self.kw_entry.delete(0, "end")
                self.render_rules()

    def save_and_close(self):
        sorter_engine.save_rules(self.rules)
        self.destroy()

def main():
    app = KQSortifyApp()
    app.mainloop()

if __name__ == "__main__":
    main()
