import os
import socket
import sys
import tempfile
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mini_webserver.core.server import (ServerController, ServerError, list_html, suggest_page,
                                        validate_folder, validate_port)
from mini_webserver.utils import net, paths, settings


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def write(folder, name, text="x"):
    with open(os.path.join(folder, name), "w", encoding="utf-8") as fh:
        fh.write(text)


class ValidationTests(unittest.TestCase):
    def test_port(self):
        self.assertEqual(validate_port(" 8080 "), 8080)
        for bad in ("abc", "", "0", "70000", "-1"):
            with self.assertRaises(ServerError):
                validate_port(bad)

    def test_folder(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(validate_folder(d), os.path.abspath(d))
            with self.assertRaises(ServerError):
                validate_folder(os.path.join(d, "gibt-es-nicht"))
        with self.assertRaises(ServerError):
            validate_folder("   ")


class PageTests(unittest.TestCase):
    def test_suggest_and_list(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(list_html(d), [])
            self.assertEqual(suggest_page(d), "")
            write(d, "zeta.html")
            write(d, "alpha.HTM")
            write(d, "notiz.txt")
            self.assertEqual(list_html(d), ["alpha.HTM", "zeta.html"])
            self.assertEqual(suggest_page(d), "alpha.HTM")
            write(d, "index.html")
            self.assertEqual(suggest_page(d), "")


class PathTests(unittest.TestCase):
    def test_initial_folder(self):
        with tempfile.TemporaryDirectory() as base, tempfile.TemporaryDirectory() as saved:
            self.assertEqual(paths.initial_folder(saved, base), saved)      # keine HTML im App-Ordner
            write(base, "seite.html")
            self.assertEqual(paths.initial_folder(saved, base), base)       # HTML neben der App gewinnt
            self.assertEqual(paths.initial_folder("/gibt/es/nicht", base), base)
        with tempfile.TemporaryDirectory() as base:
            self.assertEqual(paths.initial_folder("/gibt/es/nicht", base), base)


class SettingsTests(unittest.TestCase):
    def test_roundtrip_and_garbage(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sub", "s.json")
            self.assertEqual(settings.load(p), settings.DEFAULTS)
            self.assertTrue(settings.save({"folder": "C:\\Web", "port": 9000}, p))
            self.assertEqual(settings.load(p), {"folder": "C:\\Web", "port": 9000})
            with open(p, "w") as fh:
                fh.write("{kaputt")
            self.assertEqual(settings.load(p), settings.DEFAULTS)
            with open(p, "w") as fh:
                fh.write('{"folder": 5, "port": "80"}')
            self.assertEqual(settings.load(p), settings.DEFAULTS)


class NetTests(unittest.TestCase):
    def test_local_ip_is_ipv4(self):
        socket.inet_aton(net.local_ip())


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        write(self.dir.name, "index.html", "<h1>Hallo</h1>")
        self.logs = []
        self.ctl = ServerController(log=self.logs.append)

    def tearDown(self):
        self.ctl.stop()
        self.dir.cleanup()

    def get(self, port, path="/"):
        return urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path), timeout=5)

    def test_serves_folder_and_logs(self):
        port = free_port()
        self.ctl.start(self.dir.name, port)
        self.assertTrue(self.ctl.running)
        with self.get(port) as resp:
            self.assertEqual(resp.read(), b"<h1>Hallo</h1>")
            self.assertEqual(resp.headers["Cache-Control"], "no-cache")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get(port, "/fehlt.html")
        self.assertEqual(cm.exception.code, 404)
        self.assertTrue(any("GET / " in line for line in self.logs), self.logs)
        self.assertTrue(any("Server gestartet" in line for line in self.logs))

    def test_no_path_traversal(self):
        port = free_port()
        self.ctl.start(self.dir.name, port)
        with self.assertRaises(urllib.error.HTTPError):
            self.get(port, "/..%2f..%2f..%2fetc/passwd")

    def test_stop_and_restart(self):
        port = free_port()
        self.ctl.start(self.dir.name, port)
        self.assertTrue(self.ctl.stop())
        self.assertFalse(self.ctl.running)
        self.assertFalse(self.ctl.stop())
        with self.assertRaises(urllib.error.URLError):
            self.get(port)
        self.ctl.start(self.dir.name, port)  # gleicher Port gleich wieder frei
        with self.get(port) as resp:
            self.assertEqual(resp.status, 200)

    def test_double_start_and_bad_input(self):
        port = free_port()
        self.ctl.start(self.dir.name, port)
        with self.assertRaises(ServerError):
            self.ctl.start(self.dir.name, port)
        self.ctl.stop()
        with self.assertRaises(ServerError):
            self.ctl.start("/gibt/es/nicht", port)
        with self.assertRaises(ServerError):
            self.ctl.start(self.dir.name, "abc")
        self.assertFalse(self.ctl.running)

    def test_port_in_use_message(self):
        blocker = socket.socket()
        blocker.bind(("0.0.0.0", 0))
        blocker.listen(1)
        try:
            with self.assertRaises(ServerError) as cm:
                self.ctl.start(self.dir.name, blocker.getsockname()[1])
            self.assertIn("belegt", str(cm.exception))
            self.assertFalse(self.ctl.running)
        finally:
            blocker.close()

    def test_warns_without_html(self):
        with tempfile.TemporaryDirectory() as empty:
            self.ctl.start(empty, free_port())
        self.assertTrue(any("keine HTML" in line for line in self.logs))


class IconTests(unittest.TestCase):
    def test_icon(self):
        from mini_webserver.utils.icon import make_icon
        for running in (True, False):
            self.assertEqual(make_icon(running, 32).size, (32, 32))


if __name__ == "__main__":
    unittest.main()
