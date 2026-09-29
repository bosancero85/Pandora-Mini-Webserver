#!/usr/bin/env bash
# Baut dist/MiniWebserver-Linux-<arch>.tar.gz (x86_64 oder arm64, z. B. Raspberry Pi)
# Voraussetzung: Python 3.9 oder neuer mit tkinter und venv
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
VENV=".venv-build"

case "$(uname -m)" in
  x86_64|amd64)  ARCH="x86_64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "Nicht unterstützte Architektur: $(uname -m)" >&2; exit 1 ;;
esac

if ! "$PYTHON" -c "import tkinter" 2>/dev/null; then
  echo "tkinter fehlt. Installation:" >&2
  echo "  Debian/Ubuntu/Kali/Raspberry Pi OS: sudo apt install python3-tk" >&2
  echo "  Fedora:                             sudo dnf install python3-tkinter" >&2
  echo "  Arch:                               sudo pacman -S tk" >&2
  exit 1
fi

if ! "$PYTHON" -m venv "$VENV"; then
  echo "venv fehlt. Debian/Ubuntu/Kali/Raspberry Pi OS: sudo apt install python3-venv" >&2
  exit 1
fi
VPY="$VENV/bin/python"

"$VPY" -m pip install --upgrade pip
"$VPY" -m pip install -r requirements.txt pyinstaller
"$VPY" -m PyInstaller --noconfirm --clean --windowed --onefile \
  --name MiniWebserver --collect-all customtkinter \
  --hidden-import pystray._xorg main.py

tar -C dist -czf "dist/MiniWebserver-Linux-${ARCH}.tar.gz" MiniWebserver

echo
echo "Fertig: dist/MiniWebserver-Linux-${ARCH}.tar.gz"
echo "Entpacken:  tar -xzf dist/MiniWebserver-Linux-${ARCH}.tar.gz"
echo "Starten:    ./MiniWebserver   (in den Ordner deines HTML-Projekts kopieren)"
