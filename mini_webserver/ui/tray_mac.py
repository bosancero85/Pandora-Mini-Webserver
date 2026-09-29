"""Menüleisten-Symbol für macOS, direkt über AppKit (pyobjc).

Warum nicht pystray: Auf macOS müssen alle AppKit-Aufrufe im Hauptthread laufen. Tk belegt den
Hauptthread, und pystray ändert AppKit-Objekte aus Nebenthreads, was auf neueren macOS-Versionen
abstürzen kann (pystray-Issue #195). Hier läuft alles im Hauptthread, also in der Tk-Schleife:
Menüklicks kommen über die Ereignisschleife von Tk an, die auf macOS die von AppKit ist.

Alle Methoden dürfen nur aus dem Hauptthread aufgerufen werden (das tut die App ohnehin).
"""
from __future__ import annotations

import io
from typing import Callable

_ICON_POINTS = 18  # Höhe des Symbols in der Menüleiste


def _load():
    """Lädt pyobjc erst bei Bedarf. Wirft ImportError, wenn es fehlt."""
    import objc
    from AppKit import NSImage, NSMenu, NSMenuItem, NSStatusBar
    from Foundation import NSData, NSObject
    return objc, NSImage, NSMenu, NSMenuItem, NSStatusBar, NSData, NSObject


def _make_target_class(objc, NSObject):
    """Objective-C-Ziel für die Menüeinträge. Cocoa hält Ziele nur schwach, daher muss die App es festhalten."""

    class MiniWebserverMenuTarget(NSObject):
        def initWithCallbacks_(self, callbacks):
            self = objc.super(MiniWebserverMenuTarget, self).init()
            if self is None:
                return None
            self._callbacks = callbacks
            return self

        def show_(self, sender):
            self._callbacks["show"]()

        def toggle_(self, sender):
            self._callbacks["toggle"]()

        def quit_(self, sender):
            self._callbacks["quit"]()

    return MiniWebserverMenuTarget


class MacStatusItem:
    def __init__(self, on_show: Callable[[], None], on_toggle: Callable[[], None],
                 on_quit: Callable[[], None], is_running: Callable[[], bool], make_icon):
        self._callbacks = {"show": on_show, "toggle": on_toggle, "quit": on_quit}
        self._is_running = is_running
        self._make_icon = make_icon
        self._item = None
        self._target = None
        self._toggle_item = None
        self._bar = None
        self._ns = None

    def start(self) -> bool:
        """Legt das Symbol an. Gibt False zurück, wenn pyobjc fehlt oder etwas schiefgeht."""
        try:
            objc, NSImage, NSMenu, NSMenuItem, NSStatusBar, NSData, NSObject = self._ns = _load()
            self._target = _make_target_class(objc, NSObject).alloc().initWithCallbacks_(self._callbacks)
            menu = NSMenu.alloc().init()

            def add(title, action):
                entry = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, "")
                entry.setTarget_(self._target)
                menu.addItem_(entry)
                return entry

            add("Fenster öffnen", "show:")
            self._toggle_item = add(self._toggle_title(), "toggle:")
            menu.addItem_(NSMenuItem.separatorItem())
            add("Beenden", "quit:")

            self._bar = NSStatusBar.systemStatusBar()
            self._item = self._bar.statusItemWithLength_(-1.0)  # NSVariableStatusItemLength
            self._item.setMenu_(menu)
            self._apply(self._is_running())
        except Exception:
            self._item = None
            return False
        return True

    def _toggle_title(self) -> str:
        return "Server stoppen" if self._is_running() else "Server starten"

    def _image(self, running: bool):
        _, NSImage, _, _, _, NSData, _ = self._ns
        buf = io.BytesIO()
        self._make_icon(running, _ICON_POINTS * 2).save(buf, format="PNG")  # 2x für Retina-Displays
        raw = buf.getvalue()
        image = NSImage.alloc().initWithData_(NSData.dataWithBytes_length_(raw, len(raw)))
        image.setSize_((_ICON_POINTS, _ICON_POINTS))
        return image

    def _apply(self, running: bool) -> None:
        button = self._item.button()
        button.setImage_(self._image(running))
        button.setToolTip_("Mini Webserver: läuft" if running else "Mini Webserver: gestoppt")
        self._toggle_item.setTitle_("Server stoppen" if running else "Server starten")

    def update(self, running: bool) -> None:
        if self._item is None:
            return
        try:
            self._apply(running)
        except Exception:
            pass

    def stop(self) -> None:
        if self._item is None:
            return
        try:
            self._bar.removeStatusItem_(self._item)
        except Exception:
            pass
        self._item = None
