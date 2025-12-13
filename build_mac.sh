#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

VENV=".venv"
PYTHON="python3"

if [ ! -d "$VENV" ]; then
  $PYTHON -m venv "$VENV"
fi
source "$VENV/bin/activate"

python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller --name "Prompt" --windowed --onedir \
  --add-data "assets/app_icon.png:assets" \
  main.py

echo "构建完成：dist/Prompt.app"
