"""Guard the recovered batches and the next model/ensemble landing layers.

Checks cover content contracts and navigation, not instrument availability,
ranking or a claim that different titles alone prevent search competition.
"""
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import re
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import site_core as core

RECOVERED = {
    '99f-recorder-ukulele-voices.json': 7,
    '99g-electric-strings-free-reeds.json': 7,
    '99h-guitar-task-landings.json': 12,
    '99i-percussion-task-landings.json': 12,
    '99j-wind-task-landings.json': 12,
    '99k-keyboard-production-landings.json': 12,
    '99l-east-asian-voices.json': 10,
    '99m-brass-task-landings.json': 10,
    '99n-harp-bellows-landings.json': 10,
    '99o-historical-electric-string-landings.json': 10,
    '99p-traditional-task-landings.json': 10,
    '99q-performance-models.json': 10,
}
ADDED = {
    '99r-wind-model-landings.json': 8,
    '99s-guitar-model-landings.json': 8,
    '99t-stage-and-drum-model-landings.json': 8,
    '99u-traditional-performance-landings.json': 8,
    '99v-ensemble-preparation-landings.json': 8,
}
COMMERCIAL = re.compile(r'\b(?:аренд\w*|прокат\w*|напрокат)\b', re.I)


class RecoveryLandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temporary.name)
        cls.report = core.build(ROOT, cls.output)
        cls.documents = {name: core.read_json(ROOT / 'content/sections' / name, {})
                         for name in {**RECOVERED, **ADDED}}
        cls.records = [p for d in cls.documents.values() for p in d['pages']]
        cls.current = {p['slug']: p for p in cls.report['pages']}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @lru_cache(maxsize=None)
    def page(self, url):
        return core.soup((self.output / url.strip('/') / 'index.html').read_text(encoding='utf-8'))

    def test_recovered_and_added_batches_have_distinct_subjects(self):
        for name, expected in {**RECOVERED, **ADDED}.items():
            with self.subTest(file=name):
                self.assertEqual(len(self.documents[name]['pages']), expected)
        self.assertEqual(sum(RECOVERED.values()), 122)
        self.assertEqual(sum(ADDED.values()), 40)
        self.assertEqual(len({p['slug'] for p in self.records}), 162)

    def test_request_and_editorial_roles_are_not_interchanged(self):
        for record in self.records:
            with self.subTest(slug=record['slug']):
                entry = self.page('/' + record['slug'] + '/')
                deep = self.page('/details/' + record['slug'] + '/')
                current = self.current[record['slug']]
                self.assertEqual(core.text(entry.h1), current['entry_title'])
                self.assertEqual(core.text(deep.h1), current['editorial_title'])
                self.assertNotEqual(current['entry_title'], current['editorial_title'])
                self.assertIsNotNone(COMMERCIAL.search(current['entry_title']))
                self.assertIsNone(COMMERCIAL.search(current['editorial_title']))
                self.assertIsNone(entry.find('meta', attrs={'name': 'robots'}))
                self.assertNotIn('noindex', core.meta(deep, 'robots').casefold())
                self.assertEqual(entry.select_one('.site-footer a')['href'],
                                 '/details/' + record['slug'] + '/')

    def test_every_record_contains_real_content_and_source_references(self):
        for record in self.records:
            with self.subTest(slug=record['slug']):
                self.assertEqual(len(record['blocks']), 3)
                self.assertEqual([b['label'][:2] for b in record['blocks']], ['01', '02', '03'])
                self.assertTrue(core.text(core.soup(' '.join(record['intro']))))
                self.assertTrue(record['quote'])
                self.assertTrue(record['sources'])
                for source in record['sources']:
                    self.assertEqual(urlsplit(source['url']).scheme, 'https')
                    self.assertTrue(source['title'])
                for block in record['blocks']:
                    self.assertTrue(block['title'])
                    self.assertTrue(all(core.text(core.soup(p)) for p in block['paragraphs']))

    def test_new_paragraphs_are_not_exact_copies_within_the_batch(self):
        seen = {}
        for name in ADDED:
            for record in self.documents[name]['pages']:
                for block in record['blocks']:
                    for paragraph in block['paragraphs']:
                        value = re.sub(r'\s+', ' ', core.text(core.soup(paragraph))).casefold()
                        self.assertNotIn(value, seen, (record['slug'], seen.get(value)))
                        seen[value] = record['slug']

    def test_declared_routes_and_parent_returns_survive(self):
        for doc in self.documents.values():
            for parent, items in doc.get('navigation', {}).items():
                actual = {a['href'] for a in self.page('/details/' + parent + '/').select('#razdely a[href]')}
                for item in items:
                    with self.subTest(parent=parent, href=item['href']):
                        self.assertIn(item['href'], actual)
                        self.assertNotIn('/karta/', item['href'])
                        self.assertIsNotNone(self.page(item['href']).select_one('.range-grid'))
        for record in self.records:
            deep = self.page('/details/' + record['slug'] + '/')
            self.assertEqual(deep.select_one('.site-footer a')['href'],
                             '/details/' + record['parent'] + '/')

    def test_one_contact_and_masthead_for_all_new_routes(self):
        reference = str(self.page('/').select_one('.contact'))
        for record in self.records:
            with self.subTest(slug=record['slug']):
                for route in ('/' + record['slug'] + '/', '/details/' + record['slug'] + '/'):
                    doc = self.page(route)
                    self.assertEqual(str(doc.select_one('.contact')), reference)
                    self.assertEqual(len(doc.select('.site-footer')), 1)
                deep = self.page('/details/' + record['slug'] + '/')
                self.assertEqual(deep.select_one('.wordmark').get_text(strip=True), 'ONTOS.RENT')
                self.assertEqual(deep.select_one('.meta a')['href'], '/')
                nav = deep.select_one('#razdely')
                arguments = deep.select_one('.arguments')
                if nav:
                    order = list(deep.descendants)
                    self.assertLess(order.index(nav), order.index(arguments))

    def test_content_layers_do_not_replace_existing_layout_or_navigation(self):
        for doc in self.documents.values():
            self.assertNotIn('navigation_replace', doc)
            self.assertTrue(all('mode' not in p for p in doc['pages']))
        expected = {
            'assets/canon.css': '04fd0f6c6ff73b23eb9676765fe3d94d7921e9b83800d920615146799ea8e12f',
            'scripts/site_core.py': '01a4af94326065d30cfddfaf7974c7763ba3a9f81911add3ca84052caea36256',
        }
        for path, digest in expected.items():
            self.assertEqual(sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)

    def test_model_variants_keep_material_distinctions_explicit(self):
        lookup = {p['slug']: p for p in self.records}
        markers = {
            'yamaha-yhr567-v-arendu': ['YHR-567D', 'фиксированный'],
            'yamaha-yep201-v-arendu': ['тремя', 'четвёртого'],
            'nord-stage-4-v-arendu': ['Compact', 'USB'],
            'nord-electro-6d-v-arendu': ['6 HP', '6D'],
            'korg-sv2-v-arendu': ['SV-2S', 'SV-2 Editor'],
            'yamaha-dtx6k3x-v-arendu': ['KP90', 'резиновую', 'K2-X'],
            'alesis-nitro-max-v-arendu': ['Bluetooth', 'программ'],
        }
        for slug, expected in markers.items():
            doc = self.page('/details/' + slug + '/')
            content = core.text(doc.select_one('main'))
            for marker in expected:
                self.assertIn(marker, content, slug)


if __name__ == '__main__':
    unittest.main()
