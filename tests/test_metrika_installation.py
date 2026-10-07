"""Tests for silent post-build analytics installation, including all page roles."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import install_metrika as tracker


class MetrikaInstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        self.pages = {}
        for route in ('/', '/details/', '/royal/', '/details/royal/', '/usloviya/srok-arendy/'):
            path = self.site / route.strip('/') / 'index.html'
            path.parent.mkdir(parents=True, exist_ok=True)
            html = '<!doctype html><html lang="ru"><head><title>ONTOS.RENT</title></head><body class="entry-page"><main><h1>Заголовок</h1><p>Полезный текст</p></main></body></html>'
            path.write_text(html, encoding='utf-8')
            self.pages[route] = (path, html)
        self.redirect = self.site / 'old' / 'index.html'
        self.redirect.parent.mkdir()
        self.redirect.write_text('<html><head><meta http-equiv="refresh" content="0;url=/royal/"></head><body>Переход</body></html>', encoding='utf-8')

    def test_all_live_page_roles_receive_one_invisible_counter(self):
        result = tracker.process_site(self.site)
        self.assertEqual((result['documents'], result['redirects'], result['changed']), (5, 1, 5))
        for route, (path, original) in self.pages.items():
            with self.subTest(route=route):
                html = path.read_text(encoding='utf-8')
                self.assertEqual(tracker.counter_errors(html), [])
                self.assertIn('style="position:absolute;left:-9999px"', html)
                self.assertNotIn('informer', html.lower())
                self.assertIn('<main><h1>Заголовок</h1><p>Полезный текст</p></main>', html)
                self.assertEqual(html.split('<main>', 1)[1], original.split('<main>', 1)[1])
        self.assertNotIn(tracker.MARKER, self.redirect.read_text(encoding='utf-8'))
        self.assertEqual(tracker.process_site(self.site, check=True)['errors'], 0)

    def test_second_installation_is_idempotent(self):
        tracker.process_site(self.site)
        prior = {r: p.read_bytes() for r, (p, _) in self.pages.items()}
        self.assertEqual(tracker.process_site(self.site)['changed'], 0)
        self.assertEqual(prior, {r: p.read_bytes() for r, (p, _) in self.pages.items()})

    def test_check_fails_on_incomplete_coverage(self):
        tracker.process_site(self.site)
        self.pages['/royal/'][0].write_text(self.pages['/royal/'][1], encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'royal/index.html'):
            tracker.process_site(self.site, check=True)

    def test_incomplete_or_foreign_snippet_is_not_duplicated(self):
        with self.assertRaisesRegex(ValueError, 'Existing or incomplete'):
            tracker.inject_html('<html><head><script src="https://mc.yandex.ru/metrika/tag.js"></script></head><body></body></html>')

    def test_does_not_pretend_partial_html_is_a_valid_document(self):
        with self.assertRaisesRegex(ValueError, 'head and body'):
            tracker.inject_html('<html><head></head><p>missing body</p></html>')


if __name__ == '__main__':
    unittest.main()
