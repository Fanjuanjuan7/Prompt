@echo off
setlocal EnableExtensions EnableDelayedExpansion
pushd "%~dp0"

set "VENV=.venv"
set "PY="

for /f "delims=" %%I in ('where py 2^>nul') do set "PY=py"
if not defined PY for /f "delims=" %%I in ('where python 2^>nul') do set "PY=python"
if not defined PY (
  echo 未找到 Python，可从 https://www.python.org/ 安装
  goto :end
)

if not exist "%VENV%\Scripts\python.exe" (
  %PY% -m venv "%VENV%"
)

call "%VENV%\Scripts\activate.bat"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install pyinstaller

python -m PyInstaller --name "Prompt" --windowed --onefile ^
  --add-data "assets\app_icon.ico;assets" ^
  main.py

if exist "dist\Prompt.exe" (
  echo 构建完成：dist\Prompt.exe
) else (
  echo 构建失败，请检查上述输出信息
)

:end
popd
endlocal
