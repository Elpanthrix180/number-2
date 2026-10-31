@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python -m onix_core.interface.consola
pause
