"""Favicon semantics and publication without changing visible text or redirects."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import install_favicon as fav


class FaviconTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.site = Path(self.tmp.name)
        self.source = '''<!doctype html><html lang="ru"><head><title>Аренда скрипки</title>
<meta name="description" content="Точно про скрипку"></head><body>
<main><h1>Скрипка</h1><p>Выбор размера.</p></main></body></html>'''
        for route in ("", "details/skripka", "usloviya/srok-arendy"):
            dest = self.site / route / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(self.source, encoding="utf-8")
        self.redirect = self.site / "old" / "index.html"
        self.redirect.parent.mkdir(parents=True, exist_ok=True)
        self.redirect.write_text('<html><head><meta http-equiv="refresh" content="0;url=/"></head><body></body></html>', encoding="utf-8")

    def test_inserts_one_icon_link_set_without_changing_content(self):
        report = fav.publish(self.site)
        self.assertEqual((report["documents"], report["redirects_unchanged"], report["html_with_new_favicon"]), (3, 1, 3))
        for route in ("", "details/skripka", "usloviya/srok-arendy"):
            doc = (self.site / route / "index.html").read_text(encoding="utf-8")
            self.assertEqual(doc.count(fav.MARKER), 1)
            self.assertIn('<title>Аренда скрипки</title>', doc)
            self.assertIn('<h1>Скрипка</h1><p>Выбор размера.</p>', doc)
            self.assertIn('href="/favicon.svg"', doc)
            self.assertIn('href="/favicon.ico"', doc)
        self.assertNotIn(fav.MARKER, self.redirect.read_text(encoding="utf-8"))

    def test_favicon_assets_have_real_supported_formats(self):
        assets = fav.verify_assets()
        self.assertIn(b"<svg", assets["favicon.svg"])
        ico = assets["favicon.ico"]
        self.assertEqual(struct.unpack("<HHH", ico[:6]), (0, 1, 3))
        sizes = [ico[6 + 16 * i] for i in range(3)]
        self.assertEqual(sizes, [16, 32, 48])
        self.assertEqual((self.site / "favicon.svg").exists(), False)
        fav.publish(self.site)
        self.assertEqual((self.site / "favicon.svg").read_bytes(), assets["favicon.svg"])
        self.assertEqual((self.site / "favicon.ico").read_bytes(), assets["favicon.ico"])

    def test_idempotent_and_check_mode(self):
        fav.publish(self.site)
        self.assertEqual(fav.publish(self.site)["html_with_new_favicon"], 0)
        self.assertEqual(fav.publish(self.site, check=True)["html_with_new_favicon"], 0)

    def test_check_fails_if_icon_missing(self):
        fav.publish(self.site)
        (self.site / "favicon.ico").unlink()
        with self.assertRaisesRegex(ValueError, "Incorrect published icon"):
            fav.publish(self.site, check=True)

    def test_conflicting_icon_is_rejected(self):
        target = self.site / "index.html"
        target.write_text(self.source.replace("</head>", '<link rel="icon" href="/other.ico"></head>'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Existing conflicting favicon"):
            fav.publish(self.site)


if __name__ == "__main__":
    unittest.main()
