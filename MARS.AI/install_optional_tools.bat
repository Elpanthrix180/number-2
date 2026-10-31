@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Herramienta opcional: QUITAR FONDO con IA (rembg, licencia MIT).
echo Instala ~100 MB de librerias y, la primera vez que la uses, descarga
echo el modelo U2Net (~170 MB) desde GitHub (repositorio oficial de rembg).
set /p OK="Deseas instalarla? (S/N): "
if /I not "%OK%"=="S" exit /b 0
".venv\Scripts\python.exe" -m pip install -r requirements-optional.txt
pause
