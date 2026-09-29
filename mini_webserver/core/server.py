"""Webserver-Steuerung: liefert einen Ordner per HTTP aus.

Verhält sich wie `python -m http.server <port>`, läuft aber im Programm selbst.
Dadurch braucht die fertige .exe kein installiertes Python.
"""
from __future__ import annotations

import errno
import os
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, List, Optional

LogFn = Callable[[str], None]

_ADDR_IN_USE = {errno.EADDRINUSE, 98, 48, 10048}
_NO_PERMISSION = {errno.EACCES, 13, 10013}


class ServerError(Exception):
    """Fehler mit einer Meldung, die direkt angezeigt werden kann."""


def validate_port(value) -> int:
    try:
        port = int(str(value).strip())
    except ValueError:
        raise ServerError("Der Port muss eine Zahl sein.") from None
    if not 1 <= port <= 65535:
        raise ServerError("Der Port muss zwischen 1 und 65535 liegen.")
    return port


def validate_folder(path) -> str:
    text = str(path or "").strip()
    if not text:
        raise ServerError("Bitte zuerst einen Ordner wählen.")
    folder = os.path.abspath(os.path.expanduser(text))
    if not os.path.isdir(folder):
        raise ServerError("Der Ordner existiert nicht: " + folder)
    return folder


def list_html(folder: str) -> List[str]:
    """HTML-Dateien direkt im Ordner, alphabetisch."""
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    return sorted(n for n in names
                  if n.lower().endswith((".html", ".htm")) and os.path.isfile(os.path.join(folder, n)))


def suggest_page(folder: str) -> str:
    """Dateiname für die Adresse: leer, wenn eine index-Datei existiert, sonst die erste HTML-Datei."""
    files = list_html(folder)
    if not files or any(f.lower() in ("index.html", "index.htm") for f in files):
        return ""
    return files[0]


def friendly_os_error(exc: OSError, port: int) -> str:
    code = getattr(exc, "winerror", None) or exc.errno
    if code in _ADDR_IN_USE or exc.errno in _ADDR_IN_USE:
        return "Port %d ist schon belegt. Wähle einen anderen Port oder beende das andere Programm." % port
    if code in _NO_PERMISSION or exc.errno in _NO_PERMISSION:
        return "Keine Berechtigung für Port %d. Nimm einen Port über 1024." % port
    return "Der Server konnte nicht starten: %s" % exc


def _make_handler(directory: str, log: LogFn):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def end_headers(self):
            # Beim Bearbeiten der Seite soll das Handy immer die neueste Version laden.
            self.send_header("Cache-Control", "no-cache")
            super().end_headers()

        def log_message(self, format, *args):  # noqa: A002 (Signatur der Basisklasse)
            log("%s  %s" % (self.address_string(), format % args))

    return Handler


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    # Unter Windows würde SO_REUSEADDR einen doppelt belegten Port verschleiern.
    allow_reuse_address = os.name != "nt"

    def __init__(self, address, handler, log: LogFn):
        self._log = log
        super().__init__(address, handler)

    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, BrokenPipeError, ConnectionAbortedError)):
            return  # Handy hat die Verbindung einfach geschlossen
        self._log("%s  Fehler: %s" % (client_address[0], exc))


class ServerController:
    """Startet und stoppt den Webserver. Kennt keine Oberfläche."""

    def __init__(self, log: Optional[LogFn] = None):
        self._log: LogFn = log or (lambda message: None)
        self._httpd: Optional[_Server] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.folder = ""
        self.port = 0

    @property
    def running(self) -> bool:
        return self._httpd is not None

    def start(self, folder, port) -> None:
        with self._lock:
            if self._httpd is not None:
                raise ServerError("Der Server läuft bereits.")
            folder_path = validate_folder(folder)
            port_number = validate_port(port)
            try:
                httpd = _Server(("0.0.0.0", port_number), _make_handler(folder_path, self._log), self._log)
            except OSError as exc:
                raise ServerError(friendly_os_error(exc, port_number)) from exc
            thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.2},
                                      name="http-server", daemon=True)
            thread.start()
            self._httpd, self._thread = httpd, thread
            self.folder, self.port = folder_path, port_number
        self._log("Server gestartet. Ordner: %s, Port: %d" % (folder_path, port_number))
        if not list_html(folder_path):
            self._log("Hinweis: In diesem Ordner liegt keine HTML-Datei.")

    def stop(self) -> bool:
        with self._lock:
            httpd, thread = self._httpd, self._thread
            self._httpd = self._thread = None
        if httpd is None:
            return False
        httpd.shutdown()
        httpd.server_close()
        if thread is not None:
            thread.join(timeout=3)
        self._log("Server gestoppt.")
        return True
