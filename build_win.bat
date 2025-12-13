@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set VENV=.venv

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set PY=py
) else (
  set PY=python
)

if not exist "%VENV%" (
  %PY% -m venv "%VENV%"
)

call "%VENV%\Scripts\activate.bat"
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller --name "Prompt" --windowed --onefile ^
  --add-data "assets\\app_icon.ico;assets" ^
  main.py

echo 构建完成：dist\\Prompt.exe
