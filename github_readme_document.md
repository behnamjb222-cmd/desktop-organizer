# 🗂️ Desktop Organizer

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

A lightweight, secure, and smart Python application to automatically organize cluttered Desktop, Downloads, or custom directories into well-structured folders. Available in both **GUI** (Tkinter) and **CLI** modes with zero external dependencies.

---

## ✨ Features

- **🪶 Zero External Dependencies:** Built strictly using Python's standard libraries (`tkinter`, `shutil`, `hashlib`, `json`, `threading`).
- **🛡️ 100% Safe & Non-Destructive:** No files are ever deleted or overwritten. Duplicate files are safely moved or renamed with index suffixes (e.g., `file (1).pdf`).
- **📂 Zero Empty Folders Policy:** Category folders (e.g., `Images`, `Documents`) are generated **only** when matching files are detected.
- **👁️ Dry-Run / Preview:** Preview file movements and category assignments before making actual changes.
- **↩️ Full Undo History:** Tracks up to the last 20 operations per directory with one-click restoration.
- **🔍 Duplicate Detection:** Uses SHA-256 hashing (content-based, not just filenames) to identify exact duplicate files.
- **📅 Date-Based Subfolders:** Optional organization by Year (`2026`) or Year-Month (`2026-10`) based on last modification dates.
- **⚡ Background Processing:** Multithreaded GUI ensures smooth rendering without frozen UI or non-responding windows.

---

## 📸 Screenshots

*(Replace these placeholders with your actual screenshots/GIFs)*

| GUI Overview | File Preview & Log |
|---|---|
| ![GUI Interface](assets/screenshot_gui.png) | ![Preview Mode](assets/screenshot_log.png) |

---

## 🚀 Quick Start

### Option 1: Run Pre-compiled Executable (Windows Only, No Python Required)
1. Download `DesktopOrganizer.exe` from the [Releases](../../releases) section.
2. Double-click to launch the application.

### Option 2: Run via Python
Requirements: Python 3.8+

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/desktop-organizer.git
cd desktop-organizer

# Launch Graphical Interface (GUI)
python DesktopOrganizer.py

# Launch Interactive Command-Line Interface (CLI)
python organize_desktop_pro.py
```

---

## 🗂️ Default File Categorization

| Category | File Extensions / Rules |
|---|---|
| **Images** | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.svg`, `.ico`, `.tiff`, `.heic`, `.raw` |
| **Videos** | `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.3gp` |
| **Audio** | `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.wma` |
| **Documents** | `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.odt`, `.md`, `.epub`, `.djvu` |
| **Spreadsheets**| `.xls`, `.xlsx`, `.csv`, `.ods` |
| **Presentations**| `.ppt`, `.pptx`, `.odp`, `.key` |
| **Archives** | `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`, `.xz`, `.iso` |
| **Programs** | `.exe`, `.msi`, `.apk`, `.dmg`, `.deb`, `.bat` |
| **Code** | `.py`, `.js`, `.ts`, `.html`, `.css`, `.java`, `.c`, `.cpp`, `.cs`, `.php`, `.json`, `.xml`, `.sql`, `.sh`, `.go`, `.rs`, `.ipynb` |
| **Design** | `.psd`, `.ai`, `.fig`, `.sketch`, `.xd`, `.indd`, `.dwg` |
| **Fonts** | `.ttf`, `.otf`, `.woff`, `.woff2` |
| **Screenshots** | Keyword matching in filename: `screenshot`, `screen shot`, `snip`, `اسکرین` |
| **Others** | Any unrecognized file extension |

> **Ignored automatically:** Shortcuts (`.lnk`, `.url`), system files (`desktop.ini`, `thumbs.db`, `.DS_Store`), temporary downloads (`.crdownload`, `.part`), and files modified within the last 30 seconds.

---

## ⚙️ CLI Advanced Usage

The CLI tool (`organize_desktop_pro.py`) supports flags and daemon modes:

```bash
# Dry-run on Downloads directory
python organize_desktop_pro.py --downloads --dry-run

# Organize with Year-Month subfolders and deduplication
python organize_desktop_pro.py --by-date month --dedupe move

# Watch Mode: Run automatically every 120 seconds
python organize_desktop_pro.py --watch 120

# Undo the last operation
python organize_desktop_pro.py --undo

# View execution history
python organize_desktop_pro.py --history
```

---

## 🛠️ Building Windows Executable (.exe)

You can build the executable yourself using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name DesktopOrganizer DesktopOrganizer.py
```
Or simply double-click `build_exe.bat` on Windows.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.