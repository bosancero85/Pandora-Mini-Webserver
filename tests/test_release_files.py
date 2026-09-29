"""Prüft, dass index.html, release.yml und die Build-Skripte dieselben Dateinamen benutzen."""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Diese Namen sind der Vertrag zwischen Website, Workflow und Skripten.
ASSETS = {
    "MiniWebserver-Windows-x64.exe": "build.bat",
    "MiniWebserver-macOS-arm64.zip": "build_macos.sh",
    "MiniWebserver-macOS-x86_64.zip": "build_macos.sh",
    "MiniWebserver-Linux-x86_64.tar.gz": "build_linux.sh",
    "MiniWebserver-Linux-arm64.tar.gz": "build_linux.sh",
}


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return handle.read()


class ReleaseFilesTests(unittest.TestCase):
    def test_dateinamen_in_website_und_workflow(self):
        html, workflow = read("index.html"), read(".github", "workflows", "release.yml")
        for name in ASSETS:
            self.assertIn(name, html, "fehlt in index.html: " + name)
            self.assertIn(name, workflow, "fehlt in release.yml: " + name)

    def test_build_skripte_erzeugen_die_namen(self):
        for name, script in ASSETS.items():
            text = read(script)
            if script == "build.bat":
                self.assertIn(name, text)
            else:
                prefix, _, rest = name.partition("-")  # MiniWebserver-<OS>-<arch>.<endung>
                osname = rest.split("-")[0]
                ext = name.split(".", 1)[1]
                self.assertIn("MiniWebserver-%s-" % osname, text, script)
                self.assertIn("." + ext, text, script)

    def test_skripte_haben_gueltige_shebang(self):
        for script in ("build_linux.sh", "build_macos.sh"):
            self.assertTrue(read(script).startswith("#!/usr/bin/env bash\n"), script)

    def test_workflow_grundstruktur(self):
        workflow = read(".github", "workflows", "release.yml")
        for needle in ('tags: ["v*"]', "softprops/action-gh-release", "SHA256SUMS.txt",
                       "windows-latest", "macos-15", "macos-15-intel", "ubuntu-22.04", "ubuntu-22.04-arm",
                       "contents: write"):
            self.assertIn(needle, workflow, needle)
        self.assertNotIn("\t", workflow, "Tabs sind in YAML nicht erlaubt")

    def test_website_kennt_das_repo(self):
        html = read("index.html")
        self.assertEqual(re.findall(r"const MW_REPO = '([^']+)'", html), ["bosancero85/Pandora-Mini-Webserver"])
        self.assertNotIn("dein-user", html)
        self.assertIn("https://github.com/bosancero85/Pandora-Mini-Webserver.git", html)
        self.assertIn("<!-- Download Section", html)
        self.assertIn('id="download"', html)


if __name__ == "__main__":
    unittest.main()
