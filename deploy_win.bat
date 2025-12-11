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
python main.py
