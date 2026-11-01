@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Instalador de MARS.AI
echo ============================================================
echo   MARS.AI - Instalador para Windows 11
echo   Transforma tu imaginacion en imagenes.
echo ============================================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No se encontro Python.
  echo Instala Python 3.11 o 3.12 desde https://www.python.org/downloads/windows/
  echo y marca "Add python.exe to PATH" durante la instalacion.
  pause & exit /b 1
)

echo --- Diagnostico de tu equipo ---
%PY% check_system.py
echo.

set "TORCH_INDEX=https://download.pytorch.org/whl/cpu"
set "TORCH_KIND=CPU (sin GPU NVIDIA)"
where nvidia-smi >nul 2>nul
if %errorlevel%==0 (
  set "TORCH_INDEX=https://download.pytorch.org/whl/cu126"
  set "TORCH_KIND=GPU NVIDIA (CUDA 12.6)"
)

echo Se va a instalar en la carpeta .venv (no afecta al resto del sistema):
echo   - PyTorch para %TORCH_KIND%   (~250 MB en CPU, ~2.5 GB con CUDA)
echo   - Gradio, Diffusers, Transformers y otras librerias (~500 MB)
echo No se descarga ningun modelo de IA en este paso.
echo.
set /p OK="Deseas continuar? (S/N): "
if /I not "%OK%"=="S" ( echo Instalacion cancelada. & pause & exit /b 0 )

if not exist ".venv\Scripts\python.exe" (
  echo Creando entorno virtual...
  %PY% -m venv .venv || ( echo [ERROR] No se pudo crear el entorno virtual. & pause & exit /b 1 )
)
set "VPY=.venv\Scripts\python.exe"
"%VPY%" -m pip install --upgrade pip
echo Instalando PyTorch (%TORCH_KIND%)...
"%VPY%" -m pip install torch --index-url %TORCH_INDEX% || ( echo [ERROR] Fallo al instalar PyTorch. & pause & exit /b 1 )
echo Instalando el resto de dependencias...
"%VPY%" -m pip install -r requirements.txt || ( echo [ERROR] Fallo al instalar dependencias. & pause & exit /b 1 )

echo.
echo Comprobando la instalacion...
"%VPY%" -m pytest -q tests 2>nul || "%VPY%" -c "import torch, diffusers, gradio; print('OK: torch', torch.__version__, '| CUDA:', torch.cuda.is_available())"

echo.
set /p SC="Crear acceso directo en el escritorio? (S/N): "
if /I "%SC%"=="S" (
  powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\MARS.AI.lnk'); $s.TargetPath='%~dp0run_windows.bat'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%~dp0assets\marsai.ico'; $s.Save()"
)
echo.
echo ============================================================
echo  Instalacion completada. Ejecuta run_windows.bat para abrir MARS.AI.
echo  Despues ve a "Modelos IA" y descarga Stable Diffusion 1.5 (2.6 GB)
echo  o configura un token de Hugging Face en "Configuracion".
echo ============================================================
pause
