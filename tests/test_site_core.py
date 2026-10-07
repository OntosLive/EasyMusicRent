"""Regression tests for decisions approved in the project canon."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import site_core as core
from validate_site import validate


class CanonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temporary.name)
        cls.report = core.build(ROOT, cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def page(self, route):
        return core.soup((self.output / route.strip('/') / 'index.html').read_text())

    def test_complete_release_graph(self):
        self.assertEqual(validate(self.output, self.report)['errors'], [])

    def test_synthesizer_two_contracts(self):
        entry = self.page('/sintezatory/')
        deep = self.page('/details/sintezatory/')
        self.assertEqual(core.text(entry.h1), 'Аренда синтезаторов в Москве')
        self.assertEqual(core.text(deep.h1), 'Синтезаторы')
        self.assertEqual(core.text(deep.select_one('.wordmark')), 'ONTOS . RENT')
        self.assertNotIn('noindex', core.meta(deep, 'robots').casefold())

    def test_model_title_is_not_editorial_sentence(self):
        entry = self.page('/yamaha-p115-v-arendu/')
        self.assertEqual(core.text(entry.h1), 'Yamaha P-115 в аренду в Москве')
        self.assertLess(len(core.text(entry.h1)), 60)

    def test_conditions_have_real_icons_independent_of_footer(self):
        condition = self.page('/usloviya/srok-arendy/')
        self.assertEqual(len(condition.select('.contact-icons svg')), 2)
        self.assertEqual(len(condition.select('.site-footer')), 1)
        self.assertEqual(condition.select_one('.site-footer a')['href'], '/')

    def test_retired_urls_do_not_create_another_access_pair(self):
        old = self.page('/klavishnye/karta/')
        redirect = old.find('meta', attrs={'http-equiv':'refresh'})
        self.assertIsNotNone(redirect)
        self.assertIn('/details/klavishnye/', redirect['content'])
        self.assertIsNone(old.find('h1'))

    def test_all_mature_scene_links_survive(self):
        aliases = core.read_json(ROOT / 'content/aliases.json', {})
        for slug in ('cifrovoe-pianino', 'skripka', 'violonchel', 'kontrabas'):
            old = core.soup((ROOT / slug / 'karta/index.html').read_text())
            expected = {aliases.get(core.url_slug(a['href']), core.url_slug(a['href'])) for a in old.select('.fund-scenes a[href]')}
            actual = {core.url_slug(a['href']) for a in self.page('/details/' + slug + '/').select('#razdely a[href]')}
            self.assertTrue(expected - {slug} <= actual, (slug, expected - actual))

    def test_no_internal_directories(self):
        for name in core.INTERNAL:
            self.assertFalse((self.output / name).exists())

    def test_one_css_generation(self):
        files = [self.page('/'), self.page('/details/'), self.page('/sintezatory/'), self.page('/details/sintezatory/'), self.page('/usloviya/srok-arendy/')]
        styles = {p.find('link', rel='stylesheet')['href'] for p in files}
        self.assertEqual(len(styles), 1)

    def test_editorial_navigation_stays_in_editorial_layer(self):
        deep = self.page('/details/')
        hrefs = {a['href'] for a in deep.select('#razdely a[href]')}
        self.assertIn('/details/klavishnye/', hrefs)
        self.assertNotIn('/klavishnye/', hrefs)

    def test_entry_range_grid_keeps_four_two_one_responsive_contract(self):
        css = (ROOT / 'assets/canon.css').read_text(encoding='utf-8')
        self.assertIn('.range-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr))', css)
        self.assertIn('@media(max-width:820px){.range-grid{grid-template-columns:repeat(2,minmax(0,1fr))', css)
        self.assertIn('@media(max-width:480px){.range-grid{grid-template-columns:1fr}', css)

    def test_indexnow_key_is_published(self):
        key = (ROOT / 'content/indexnow-key.txt').read_text(encoding='utf-8').strip()
        self.assertGreaterEqual(len(key), 8)
        self.assertEqual((self.output / f'{key}.txt').read_text(encoding='utf-8').strip(), key)


if __name__ == '__main__':
    unittest.main()
