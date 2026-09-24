<div align="center">
  <img src="assets/banner.jpg" alt="KQ Sortify Hero Banner" width="100%" />
</div>

<br/>

<div align="center">
  <p><strong>Intelligent, Rule-Based Desktop File Organizer with Dark Mode GUI & Smooth Animations</strong></p>

  <a href="https://github.com/KnapQiProton/KQ-Sortify/releases/latest/download/KQ_Sortify.exe">
    <img src="https://img.shields.io/badge/⚡%20Download-KQ__Sortify.exe%20(v1.0.0)-2563eb?style=for-the-badge&logo=windows&logoColor=white" alt="Download KQ Sortify" height="38"/>
  </a>
  <a href="https://github.com/KnapQiProton/KQ-Sortify/releases/latest/download/KQ_Sortify-v1.0.0-Windows.zip">
    <img src="https://img.shields.io/badge/📦%20Download-.ZIP%20Package-3f3f46?style=for-the-badge&logo=zip&logoColor=white" alt="Download ZIP" height="38"/>
  </a>

  <br/><br/>

  [![GitHub Release](https://img.shields.io/github/v/release/KnapQiProton/KQ-Sortify?color=10b981&label=Latest%20Release)](https://github.com/KnapQiProton/KQ-Sortify/releases/latest)
  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
  [![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://customtkinter.tomschimansky.com/)
  [![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://microsoft.com/windows)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
</div>

---

## 📸 Interface Preview

<div align="center">
  <img src="assets/preview.png" alt="KQ Sortify GUI Preview" width="100%" />
  <p><em>Modern Dark Mode Interface featuring Real-Time Bilingual Toggle (ID / EN), Safe Dry-Run, Stats Dashboard & Category Pills</em></p>
</div>

---

## 🌟 Overview

**KQ Sortify** is a lightweight, rule-based file organizer that turns cluttered folders into organized ones. It scans filenames and file extensions, matches them to custom rules, and automatically moves files into categorized destination folders.

You can define your own keywords, categories, and folder structure, making KQ Sortify flexible for personal use, office work, school files, project directories, or any messy folder that needs order.

No more manual sorting. Create your rules once, run KQ Sortify, and let it handle the cleanup!

---

## ✨ Features

- 🎨 **Modern Dark Mode GUI**: Built with CustomTkinter featuring smooth 60+ FPS ease-out hover animations, luminous border glow, and tactile click feedback.
- 🌐 **Bilingual Support (ID / EN)**: Instant one-click switch between **Indonesian 🇮🇩** and **English 🌐** across the entire interface.
- 🛡️ **Safe Dry-Run & Interactive Preview**: Preview all files, target destinations, sizes, and dates before moving anything. Deselect any files you wish to keep intact.
- ↩️ **One-Click Undo (Rollback)**: Made a mistake? Revert sorted files back to their exact original locations anytime with full batch history journaling.
- ⚡ **Lightweight & High Performance**: 60 FPS buttery-smooth scrolling with native dark table view and bounded size sampling that never freezes or triggers "Not Responding".
- ⚙️ **Smart Prioritized Classification**:
  - 🎓 **Kuliah / College**: Keywords prioritized (`tugas`, `materi`, `kalkulus`, `alpro`, `thesis`, etc.)
  - 💻 **Coding**: Source code (`.py`, `.cpp`, `.js`, `.ts`, `.html`, `.css`, etc.)
  - 🎮 **Games**: Game setups, ISOs, and ROMs (`.iso`, `.rom`, `fitgirl`, `repack`, `steam`, etc.)
  - 📄 **Documents**: PDFs, Word, Excel, Presentations, and Text files.
  - 📦 **Archives**: Compressed files (`.zip`, `.rar`, `.7z`, `.tar`, `.gz`).
  - 🖼️ **Media**: Images, Videos, Audio, Fonts, and 3D Assets.
  - ⚙️ **Installers**: Setup executables and packages (`.exe`, `.msi`, `.apk`).

---

## 🚀 Quick Start (Cara Menjalankan)

### 📥 Option 1: Standalone Executable (Cara Termudah - Langsung Pakai)
Bagi pengguna yang ingin langsung memakai tanpa perlu install Python atau mengetik perintah apapun:
1. **Download langsung**:
   - ⚡ **[Download KQ_Sortify.exe (Direct Download)](https://github.com/KnapQiProton/KQ-Sortify/releases/latest/download/KQ_Sortify.exe)**
   - 📦 **[Download Paket .ZIP Lengkap](https://github.com/KnapQiProton/KQ-Sortify/releases/latest/download/KQ_Sortify-v1.0.0-Windows.zip)**
2. **Jalankan**: Klik 2x file `KQ_Sortify.exe`.
3. Selesai! Aplikasi langsung terbuka dan siap merapikan folder Anda.

### 💻 Option 2: Run from Python Source
Bagi developer yang ingin menjalankan atau memodifikasi source code Python:
1. Clone the repository:
   ```bash
   git clone https://github.com/KnapQiProton/KQ-Sortify.git
   cd KQ-Sortify
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the GUI:
   ```bash
   python gui.py
   ```

---

## 🛠️ Building the Standalone Executable

To compile `KQ_Sortify.exe` from source using PyInstaller:

```bash
python -m PyInstaller --noconfirm --onefile --windowed --icon=logo.ico --name="KQ_Sortify" --add-data "logo.png;." --add-data "logo.ico;." --add-data "rules_config.json;." --collect-all customtkinter gui.py
```

---

## 📁 Project Structure

```
KQ Sortify/
│
├── assets/                    # Project Screenshots & Banners
│   ├── banner.jpg             # Hero Banner Image
│   └── preview.png            # GUI Interface Screenshot
├── KQ_Sortify.exe             # Standalone Windows Executable
├── Jalankan_KQ_Sortify.bat    # Quick Launcher Batch Script
├── gui.py                     # CustomTkinter Dark Mode GUI & Animations
├── sorter_engine.py           # Core File Scanning & Sorting Engine
├── rules_config.json          # Customizable Category Rules & Saved Language
├── logo.png                   # High-Resolution App Logo
├── logo.ico                   # Windows App Icon
├── requirements.txt           # Python Dependencies
├── .gitignore                 # Git Ignore Configuration
└── README.md                  # Project Documentation
```

---

## 🤝 Contributing & License

Contributions, feedback, and suggestions are welcome! Feel free to open an Issue or submit a Pull Request.

Distributed under the MIT License. Developed with care by [KnapQi](https://github.com/KnapQiProton).
