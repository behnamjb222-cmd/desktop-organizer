@echo off
chcp 65001 >nul
title ساخت فایل exe
echo ============================================
echo   ساخت DesktopOrganizer.exe
echo ============================================
python --version >nul 2>&1
if errorlevel 1 (
  echo Python پیدا نشد! از https://www.python.org/downloads نصبش کن
  echo و حتما تیک "Add Python to PATH" را بزن.
  pause
  exit /b 1
)
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "DesktopOrganizer" organize_desktop_gui.py
if errorlevel 1 (
  echo ساخت ناموفق بود.
  pause
  exit /b 1
)
echo.
echo ✅ تمام شد! فایل اجرایی اینجاست:  dist\DesktopOrganizer.exe
pause
