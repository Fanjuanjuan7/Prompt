#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PY="python3"
VENV=".venv"

if [ ! -d "$VENV" ]; then
  $PY -m venv "$VENV"
fi

source "$VENV/bin/activate"
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
exec python main.py
