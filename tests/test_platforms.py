"""Tests für die Plattform-Anpassungen (macOS, Linux, Windows) und das Symbol-Format."""
import os
import sys
import tempfile
import types
import unittest
from types import SimpleNamespace
from unittest import mock


class TrayPlatformTests(unittest.TestCase):
    def _fake_pystray(self):
        icon = mock.MagicMock()
        return SimpleNamespace(
            Icon=mock.MagicMock(return_value=icon),
            Menu=mock.MagicMock(),
            MenuItem=mock.MagicMock(),
        ), icon

    def _make_tray(self):
        from mini_webserver.ui import tray as tray_mod
        return tray_mod, tray_mod.Tray(lambda: None, lambda: None, lambda: None, lambda: False)

    def test_pystray_unter_linux_und_windows(self):
        for platform in ("linux", "win32"):
            tray_mod, tray = self._make_tray()
            fake, icon = self._fake_pystray()
            with mock.patch.object(tray_mod, "pystray", fake), \
                    mock.patch.object(tray_mod, "make_icon", lambda running: None), \
                    mock.patch.object(sys, "platform", platform):
                self.assertTrue(tray.start(), platform)
            self.assertTrue(tray.available)
            icon.run_detached.assert_called_once()

    def test_macos_nutzt_pystray_nicht(self):
        tray_mod, tray = self._make_tray()
        fake, icon = self._fake_pystray()
        item = mock.MagicMock()
        item.start.return_value = True
        with mock.patch.object(tray_mod, "pystray", fake), \
                mock.patch.object(tray_mod, "make_icon", lambda running, size=64: None), \
                mock.patch.object(sys, "platform", "darwin"), \
                mock.patch("mini_webserver.ui.tray_mac.MacStatusItem", return_value=item):
            self.assertTrue(tray.start())
            self.assertTrue(tray.available)
            fake.Icon.assert_not_called()
            tray.update(True)
            item.update.assert_called_once_with(True)
            tray.notify("x")  # darf nichts auslösen und nicht abstürzen
            tray.stop()
            item.stop.assert_called_once()
        self.assertFalse(tray.available)

    def test_macos_ohne_pyobjc_gibt_false_zurueck(self):
        tray_mod, tray = self._make_tray()
        with mock.patch.object(tray_mod, "make_icon", lambda running, size=64: None), \
                mock.patch.object(sys, "platform", "darwin"), \
                mock.patch.dict(sys.modules, {"objc": None, "AppKit": None, "Foundation": None}):
            self.assertFalse(tray.start())  # ImportError wird abgefangen: Schließen beendet dann das Programm
        self.assertFalse(tray.available)


class MacStatusItemTests(unittest.TestCase):
    """Prüft tray_mac mit Stellvertretern für pyobjc; echtes AppKit gibt es nur auf macOS."""

    def setUp(self):
        self.created = []

        class Base:  # Stellvertreter für NSObject
            @classmethod
            def alloc(cls):
                return cls()

            def init(self):
                return self

        objc = types.ModuleType("objc")
        objc.super = super

        class Item:
            def __init__(self, title="", action=None):
                self.title, self.action, self.target = title, action, None

            def setTarget_(self, target):
                self.target = target

            def setTitle_(self, title):
                self.title = title

        class MenuItem:
            @classmethod
            def alloc(cls):
                return SimpleNamespace(initWithTitle_action_keyEquivalent_=lambda t, a, k: Item(t, a))

            @staticmethod
            def separatorItem():
                return Item("-")

        class Menu:
            @classmethod
            def alloc(cls):
                return SimpleNamespace(init=lambda: SimpleNamespace(items=[], addItem_=lambda e: outer.items.append(e)))

        outer = self
        self.items = []
        self.button = SimpleNamespace(images=[], tips=[])
        self.button.setImage_ = self.button.images.append
        self.button.setToolTip_ = self.button.tips.append
        self.status_item = SimpleNamespace(button=lambda: self.button, menu=None)
        self.status_item.setMenu_ = lambda m: setattr(self.status_item, "menu", m)
        self.removed = []
        bar = SimpleNamespace(statusItemWithLength_=lambda n: self.status_item, removeStatusItem_=self.removed.append)

        class Image:
            @classmethod
            def alloc(cls):
                return SimpleNamespace(initWithData_=lambda d: SimpleNamespace(setSize_=lambda s: None))

        appkit = types.ModuleType("AppKit")
        appkit.NSImage, appkit.NSMenu, appkit.NSMenuItem = Image, Menu, MenuItem
        appkit.NSStatusBar = SimpleNamespace(systemStatusBar=lambda: bar)
        foundation = types.ModuleType("Foundation")
        foundation.NSObject = Base
        foundation.NSData = SimpleNamespace(dataWithBytes_length_=lambda raw, n: raw)
        patcher = mock.patch.dict(sys.modules, {"objc": objc, "AppKit": appkit, "Foundation": foundation})
        patcher.start()
        self.addCleanup(patcher.stop)

        self.calls = []
        self.running = False
        from PIL import Image as PILImage
        from mini_webserver.ui.tray_mac import MacStatusItem
        self.item = MacStatusItem(lambda: self.calls.append("show"), lambda: self.calls.append("toggle"),
                                  lambda: self.calls.append("quit"), lambda: self.running,
                                  lambda running, size=64: PILImage.new("RGBA", (size, size)))

    def test_menue_und_klicks(self):
        self.assertTrue(self.item.start())
        titles = [i.title for i in self.items]
        self.assertEqual(titles, ["Fenster öffnen", "Server starten", "-", "Beenden"])
        self.assertEqual([i.action for i in self.items if i.title != "-"], ["show:", "toggle:", "quit:"])
        target = self.items[0].target
        self.assertIsNotNone(target)
        target.show_(None)
        target.toggle_(None)
        target.quit_(None)
        self.assertEqual(self.calls, ["show", "toggle", "quit"])

    def test_update_setzt_symbol_hinweis_und_menuetext(self):
        self.assertTrue(self.item.start())
        self.item.update(True)
        self.assertEqual(self.items[1].title, "Server stoppen")
        self.assertEqual(self.button.tips[-1], "Mini Webserver: läuft")
        self.item.update(False)
        self.assertEqual(self.items[1].title, "Server starten")
        self.assertEqual(self.button.tips[-1], "Mini Webserver: gestoppt")
        self.assertGreaterEqual(len(self.button.images), 3)

    def test_stop_entfernt_das_symbol(self):
        self.item.start()
        self.item.stop()
        self.assertEqual(self.removed, [self.status_item])
        self.item.update(True)  # nach stop kein Fehler
        self.item.stop()
        self.assertEqual(len(self.removed), 1)


class AppDirTests(unittest.TestCase):
    def test_macos_app_bundle_liefert_ordner_neben_der_app(self):
        from mini_webserver.utils import paths
        exe = os.path.join(os.sep, "Users", "ich", "Projekt", "MiniWebserver.app", "Contents", "MacOS", "MiniWebserver")
        with mock.patch.object(sys, "frozen", True, create=True), mock.patch.object(sys, "executable", exe):
            self.assertEqual(paths.app_dir(), os.path.join(os.sep, "Users", "ich", "Projekt"))

    def test_normale_programmdatei_liefert_ihren_ordner(self):
        from mini_webserver.utils import paths
        exe = os.path.join(os.sep, "home", "ich", "projekt", "MiniWebserver")
        with mock.patch.object(sys, "frozen", True, create=True), mock.patch.object(sys, "executable", exe):
            self.assertEqual(paths.app_dir(), os.path.join(os.sep, "home", "ich", "projekt"))


class IconFormatTests(unittest.TestCase):
    def test_formate(self):
        from PIL import Image
        from mini_webserver.utils.icon import write_icon
        with tempfile.TemporaryDirectory() as tmp:
            for name, fmt in (("icon.ico", "ICO"), ("icon.icns", "ICNS"), ("icon.png", "PNG")):
                target = os.path.join(tmp, "sub", name)
                write_icon(target)
                with Image.open(target) as img:
                    self.assertEqual(img.format, fmt, name)

    def test_unbekannte_endung(self):
        from mini_webserver.utils.icon import write_icon
        with self.assertRaises(ValueError):
            write_icon("icon.bmp")


if __name__ == "__main__":
    unittest.main()
