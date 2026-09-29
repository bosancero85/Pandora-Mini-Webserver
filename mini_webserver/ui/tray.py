"""Tray-Symbol mit Menü. Windows und Linux: pystray in eigenem Thread. macOS: Menüleiste über AppKit (tray_mac)."""
from __future__ import annotations

import sys
from typing import Callable

try:
    import pystray
    from ..utils.icon import make_icon
except Exception:  # pystray oder Pillow fehlt, oder es gibt kein Tray-Backend
    pystray = None
    make_icon = None


def _use_native_mac() -> bool:
    """Auf macOS läuft pystray nicht neben Tk (Hauptthread, pystray-Issue #195); dort gilt tray_mac."""
    return sys.platform == "darwin"


class Tray:
    def __init__(self, on_show: Callable[[], None], on_toggle: Callable[[], None],
                 on_quit: Callable[[], None], is_running: Callable[[], bool]):
        self._on_show = on_show
        self._on_toggle = on_toggle
        self._on_quit = on_quit
        self._is_running = is_running
        self._icon = None
        self._mac = None
        self.available = False

    def start(self) -> bool:
        """Zeigt das Symbol. Gibt False zurück, wenn kein Tray möglich ist."""
        if _use_native_mac():
            return self._start_mac()
        if pystray is None:
            return False
        try:
            menu = pystray.Menu(
                pystray.MenuItem("Fenster öffnen", lambda icon, item: self._on_show(), default=True),
                pystray.MenuItem(lambda item: "Server stoppen" if self._is_running() else "Server starten",
                                 lambda icon, item: self._on_toggle()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Beenden", lambda icon, item: self._on_quit()),
            )
            self._icon = pystray.Icon("mini_webserver", make_icon(False), "Mini Webserver: gestoppt", menu)
            self._icon.run_detached()
        except Exception:
            self._icon = None
            return False
        self.available = True
        return True

    def _start_mac(self) -> bool:
        if make_icon is None:
            return False
        try:
            from .tray_mac import MacStatusItem
        except Exception:
            return False
        item = MacStatusItem(self._on_show, self._on_toggle, self._on_quit, self._is_running, make_icon)
        if not item.start():
            return False
        self._mac = item
        self.available = True
        return True

    def update(self, running: bool) -> None:
        if self._mac is not None:
            self._mac.update(running)
            return
        if self._icon is None:
            return
        try:
            self._icon.icon = make_icon(running)
            self._icon.title = "Mini Webserver: läuft" if running else "Mini Webserver: gestoppt"
            self._icon.update_menu()
        except Exception:
            pass

    def notify(self, message: str) -> None:
        if self._mac is not None:
            return  # kein Hinweis-Banner unter macOS; das Symbol in der Menüleiste zeigt den Zustand
        if self._icon is None:
            return
        try:
            self._icon.notify(message, "Mini Webserver")
        except Exception:
            pass

    def stop(self) -> None:
        if self._mac is not None:
            self._mac.stop()
            self._mac = None
            self.available = False
            return
        if self._icon is None:
            return
        try:
            self._icon.stop()
        except Exception:
            pass
        self._icon = None
        self.available = False
