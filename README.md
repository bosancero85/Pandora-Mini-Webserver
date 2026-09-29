# Mini Webserver

Ein kleines Tool für Windows, macOS und Linux mit Oberfläche (CustomTkinter), das einen Ordner per HTTP im Netzwerk ausliefert. Es ersetzt den Befehl `python -m http.server 8080`: Start/Stopp per Knopf, Log der Zugriffe, Adresse fürs Handy, Tray-Symbol.

## Funktionen

- Start/Stopp-Knopf mit Ladebalken und Statusanzeige
- Ordnerauswahl per Dialog, Port einstellbar (Standard 8080)
- Log mit Zeitstempel und allen Zugriffen
- Zeigt die Adresse fürs Handy, mit Kopieren-Knopf und "Im Browser öffnen"
- Schließen legt das Fenster in den Tray. Rechtsklick auf das Symbol: Fenster öffnen, Server starten/stoppen, Beenden (unter macOS als Symbol in der Menüleiste)
- Der Server ist eingebaut. Die fertigen Programme brauchen kein installiertes Python
- Liegt die .exe im Ordner eines HTML-Projekts, wird genau dieser Ordner ausgeliefert. Sonst merkt sich das Tool den zuletzt benutzten Ordner

## Download

Fertige Programme gibt es auf der Seite der [Releases](../../releases/latest). Die `index.html` erkennt dein Betriebssystem und bietet das passende Paket an.

| System | Datei |
| --- | --- |
| Windows 10/11 (64-Bit) | `MiniWebserver-Windows-x64.exe` |
| macOS, Apple Silicon | `MiniWebserver-macOS-arm64.zip` |
| macOS, Intel | `MiniWebserver-macOS-x86_64.zip` |
| Linux x86_64 | `MiniWebserver-Linux-x86_64.tar.gz` |
| Linux arm64 (z. B. Raspberry Pi 4/5 mit 64-Bit-System) | `MiniWebserver-Linux-arm64.tar.gz` |

Zu jedem Release gehört `SHA256SUMS.txt` zum Prüfen der Downloads.

- **Windows:** `.exe` starten. SmartScreen kann warnen, weil die Datei nicht signiert ist.
- **macOS:** ZIP entpacken. Die App ist nicht signiert: beim ersten Start Rechtsklick, dann „Öffnen“. Sie kann auch neben dein HTML-Projekt gelegt werden.
- **Linux:** `tar -xzf MiniWebserver-Linux-*.tar.gz`, dann `./MiniWebserver`. Nötig ist eine grafische Oberfläche (X11 oder XWayland).

## Benutzung

1. `MiniWebserver.exe` in den Ordner mit deinem HTML-Projekt kopieren und starten (oder den Ordner im Tool wählen).
2. "Server starten" klicken. Fragt die Windows-Firewall, "Zulassen" für das private Netzwerk wählen.
3. Am Handy (gleiches WLAN) die angezeigte Adresse öffnen, zum Beispiel `http://192.168.178.40:8080/`.

Gibt es keine `index.html`, zeigt die Adresse direkt auf die erste gefundene HTML-Datei.

## Selbst bauen

Es wird immer für das System gebaut, auf dem das Skript läuft. Nötig ist Python 3.9 oder neuer mit tkinter.

| System | Befehl | Ergebnis |
| --- | --- | --- |
| Windows | `build.bat` (Doppelklick) | `dist\MiniWebserver.exe` und `dist\MiniWebserver-Windows-x64.exe` |
| macOS | `bash build_macos.sh` | `dist/MiniWebserver-macOS-<arm64\|x86_64>.zip` |
| Linux | `bash build_linux.sh` | `dist/MiniWebserver-Linux-<x86_64\|arm64>.tar.gz` |

Unter Debian, Ubuntu, Kali und Raspberry Pi OS vorher: `sudo apt install python3-tk python3-venv`. Unter macOS mit Homebrew: `brew install python-tk`.

## Release über GitHub

Die Download-Links der `index.html` zeigen auf `bosancero85/Pandora-Mini-Webserver` (Konstante `MW_REPO`). Bei einem anderen Repository nur dort ändern.

Änderungen pushen, dann einen Versions-Tag setzen:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Der Workflow `.github/workflows/release.yml` führt auf jedem System die Tests aus, baut die fünf Pakete, erzeugt `SHA256SUMS.txt` und legt alles in ein GitHub-Release. Manuell gestartet (Actions, „Release“, „Run workflow“) entstehen nur Artefakte ohne Release.

Der Workflow `.github/workflows/build.yml` baut weiter bei jedem Push die Windows-.exe als Artefakt.

Hinweise:

- Die Linux-Pakete werden auf Ubuntu 22.04 gebaut, damit sie auch auf älteren Systemen wie Debian 12 und Raspberry Pi OS Bookworm laufen.
- GitHub stellt Intel-Mac-Runner nur noch bis Herbst 2027 bereit. Danach entfällt das Intel-Paket, oder du entfernst den Eintrag `macos-15-intel` in `release.yml` und die Intel-Links in `index.html`.
- Die Pakete sind nicht signiert (siehe Hinweise unter Download).

## Aus dem Quellcode starten

```bash
pip install -r requirements.txt
python main.py
```

## Tests

```bash
python -m unittest discover -s tests
node tests/detect_os.test.js   # Betriebssystem-Erkennung der Webseite (braucht Node.js)
```

Die Kernlogik (Server, Ordner, Einstellungen) wird echt getestet. Ein weiterer Test stellt sicher, dass `index.html`, `release.yml` und die Build-Skripte dieselben Dateinamen verwenden. Die Oberfläche wird mit Stellvertreter-Modulen auf ihren Ablauf geprüft, das Aussehen nicht.

## Hinweise zur Sicherheit

- Der Server ist für alle Geräte im selben Netzwerk erreichbar. Gib nur Ordner frei, die andere sehen dürfen, und nutze das Tool nicht in fremden WLANs.
- Ohne `index.html` zeigt der Server eine Dateiliste des Ordners.
- Windows SmartScreen, macOS Gatekeeper oder Virenscanner können bei selbst gebauten Programmen warnen, weil sie nicht signiert sind.

## Lizenz

MIT, siehe [LICENSE](LICENSE).
