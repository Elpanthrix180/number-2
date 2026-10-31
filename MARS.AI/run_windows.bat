@echo off
chcp 65001 >nul
cd /d "%~dp0"
title MARS.AI
if not exist ".venv\Scripts\python.exe" (
  echo MARS.AI no esta instalado todavia. Ejecuta primero install_windows.bat
  pause & exit /b 1
)
".venv\Scripts\python.exe" main.py %*
if errorlevel 1 pause
