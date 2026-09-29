#!/usr/bin/env bash
# Baut dist/MiniWebserver-macOS-<arch>.zip mit MiniWebserver.app (arm64 oder x86_64)
# Voraussetzung: Python 3.9 oder neuer mit tkinter (Homebrew: brew install python-tk)
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
VENV=".venv-build"

case "$(uname -m)" in
  arm64)  ARCH="arm64" ;;
  x86_64) ARCH="x86_64" ;;
  *) echo "Nicht unterstützte Architektur: $(uname -m)" >&2; exit 1 ;;
esac

if ! "$PYTHON" -c "import tkinter" 2>/dev/null; then
  echo "tkinter fehlt. Mit Homebrew: brew install python-tk" >&2
  echo "Oder Python von python.org installieren (bringt tkinter mit)." >&2
  exit 1
fi

"$PYTHON" -m venv "$VENV"
VPY="$VENV/bin/python"

"$VPY" -m pip install --upgrade pip
"$VPY" -m pip install -r requirements.txt pyinstaller
"$VPY" -m mini_webserver.utils.icon assets/icon.icns
"$VPY" -m PyInstaller --noconfirm --clean --windowed \
  --name MiniWebserver --icon assets/icon.icns \
  --collect-all customtkinter \
  --hidden-import AppKit --hidden-import Foundation --hidden-import objc main.py

ditto -c -k --sequesterRsrc --keepParent dist/MiniWebserver.app "dist/MiniWebserver-macOS-${ARCH}.zip"

echo
echo "Fertig: dist/MiniWebserver-macOS-${ARCH}.zip"
echo "Die App ist nicht signiert. Beim ersten Start: Rechtsklick auf die App, dann \"Öffnen\"."
