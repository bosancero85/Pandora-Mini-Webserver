# Session-Übergabe

Stand: 2026-09-29

## Erledigt

- Kernlogik: Server im Programm (wie `http.server`), Ordner/Port-Prüfung, verständliche Fehler
- Oberfläche: Ordnerwahl, Start/Stopp, Ladebalken, Log, Adresse fürs Handy
- Tray: Schließen legt in den Tray, Menü mit Öffnen/Start-Stopp/Beenden
- Build: `build.bat` und GitHub-Workflow
- 21 Tests grün (Kernlogik echt, Oberfläche mit Stellvertreter-Modulen)
- LICENSE, README.de.md, .gitignore, Playbook, lokaler Git-Commit

## Offen

- Erster echter Lauf auf Windows: `python main.py` (Aussehen und Tray prüfen)
- .exe bauen (`build.bat` oder GitHub Actions) und einmal starten
- Repo bei GitHub anlegen und pushen

## Hinweise

- In der Entwicklungsumgebung gab es kein tkinter und kein Netz, daher wurde die echte Oberfläche nicht gezeigt
- Zugehöriges Projekt: Ollama Mobile Chat (wird mit diesem Tool ausgeliefert)
