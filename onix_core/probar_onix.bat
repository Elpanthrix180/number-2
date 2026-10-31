@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python -m unittest onix_core.tests.test_cerebro -v
pause
