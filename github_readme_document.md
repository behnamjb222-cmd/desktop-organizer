# 🗂️ Desktop Organizer

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

A lightweight, secure, and smart Python application to automatically organize cluttered Desktop, Downloads, or custom directories into well-structured folders. Available in both **GUI** (Tkinter) and **CLI** modes with zero external dependencies.

---

## ✨ Key Features

- **🪶 Zero External Dependencies:** Built strictly using Python standard libraries (`tkinter`, `shutil`, `hashlib`, `json`, `threading`).
- **🛡️ 100% Safe & Non-Destructive:** No files are ever deleted or overwritten. Duplicate files are safely moved or renamed with index suffixes (e.g., `file (1).pdf`).
- **📂 Zero Empty Folders Policy:** Category folders (e.g., `Images`, `Documents`) are generated **only** when matching files are detected.
- **👁️ Dry-Run / Preview Mode:** Preview all file movements and category assignments before making actual changes.
- **↩️ Full Undo History:** Tracks up to the last 20 operations per directory with one-click restoration.
- **🔍 Content-Based Duplicate Detection:** Uses SHA-256 hashing (not just file names) to identify exact duplicate files safely.
- **📅 Date-Based Subfolders:** Optional organization by Year (`2026`) or Year-Month (`2026-10`) based on last modification dates.
- **🌍 Full Persian / Unicode Support:** Seamlessly handles Persian file names, Persian keywords (e.g., `اسکرین`), and RTL directory structures.
- **⚡ Non-Blocking UI:** Multithreaded Tkinter interface ensures smooth execution without window freezing.

---

## 📸 Screenshots

*(Place your screenshots inside an `assets/` folder)*

| GUI Overview | File Preview & Operations Log |
|---|---|
| ![GUI Interface](assets/screenshot_gui.png) | ![Preview Mode](assets/screenshot_log.png) |

---

## 🚀 Quick Start

### Option 1: Standalone Executable (Windows Only — No Python Required)
1. Go to the **[Releases](../../releases)** page of this repository.
2. Download `DesktopOrganizer.exe`.
3. Run the executable file directly.

### Option 2: Run via Python Source Code
Requirements: **Python 3.8+**

```bash
# Clone this repository
git clone [https://github.com/YOUR_USERNAME/desktop-organizer.git](https://github.com/YOUR_USERNAME/desktop-organizer.git)
cd desktop-organizer

# Run Graphical Interface (GUI)
python DesktopOrganizer.py

# Run Interactive Command-Line Interface (CLI)
python organize_desktop_pro.py
