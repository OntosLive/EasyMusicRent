"""Guard new voice, model and final-scenario records without changing the canon.

These checks enforce source and routing contracts. They do not establish
availability, search demand, rankings, or semantic uniqueness by themselves.
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

BATCHES = {
    '99w-extended-wind-voices.json': 8,
    '99x-orchestral-plucked-voices.json': 8,
    '99y-wind-model-comparisons.json': 8,
    '99z-wind-ensemble-final-landings.json': 8,
}
COMMERCIAL = re.compile(r'\b(?:аренд\w*|прокат\w*|напрокат)\b', re.I)


class ExtendedVoiceLandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temporary.name)
        cls.report = core.build(ROOT, cls.output)
        cls.documents = {name: core.read_json(ROOT / 'content/sections' / name, {})
                         for name in BATCHES}
        cls.records = [p for d in cls.documents.values() for p in d['pages']]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @lru_cache(maxsize=None)
    def page(self, route):
        return core.soup((self.output / route.strip('/') / 'index.html').read_text(encoding='utf-8'))

    def test_batch_counts_and_distinct_subjects(self):
        for name, expected in BATCHES.items():
            self.assertEqual(len(self.documents[name]['pages']), expected, name)
        self.assertEqual(len({p['slug'] for p in self.records}), 32)
        self.assertEqual(len({p['search_title'] for p in self.records}), 32)

    def test_entry_and_editorial_contracts(self):
        for p in self.records:
            with self.subTest(slug=p['slug']):
                entry = self.page('/' + p['slug'] + '/')
                deep = self.page('/details/' + p['slug'] + '/')
                self.assertEqual(core.text(entry.h1), p['search_title'])
                self.assertEqual(core.text(deep.h1), p['editorial_title'])
                self.assertIsNotNone(COMMERCIAL.search(p['search_title']))
                self.assertIsNone(COMMERCIAL.search(p['editorial_title']))
                self.assertIsNone(entry.find('meta', attrs={'name':'robots'}))
                self.assertNotIn('noindex', core.meta(deep, 'robots').casefold())
                self.assertEqual(entry.select_one('.site-footer a')['href'], '/details/' + p['slug'] + '/')
                self.assertEqual(deep.select_one('.site-footer a')['href'], '/details/' + p['parent'] + '/')

    def test_authored_content_and_sources(self):
        paragraphs = {}
        for p in self.records:
            with self.subTest(slug=p['slug']):
                self.assertEqual(len(p['blocks']), 3)
                self.assertEqual([b['label'][:2] for b in p['blocks']], ['01','02','03'])
                self.assertTrue(p['intro'] and p['quote'] and p['description'] and p['sources'])
                combined = ' '.join(p['intro'] + [s for b in p['blocks'] for s in b['paragraphs']])
                # Presence check only, not an editorial word-count target.
                self.assertGreater(len(core.text(core.soup(combined)).split()), 100)
                for source in p['sources']:
                    self.assertEqual(urlsplit(source['url']).scheme, 'https')
                    self.assertTrue(source['title'])
                for b in p['blocks']:
                    self.assertTrue(b['title'])
                    for paragraph in b['paragraphs']:
                        normalized = re.sub(r'\s+', ' ', core.text(core.soup(paragraph))).casefold()
                        self.assertNotIn(normalized, paragraphs, (p['slug'], paragraphs.get(normalized)))
                        paragraphs[normalized] = p['slug']

    def test_declared_navigation_is_live_and_before_arguments(self):
        for doc in self.documents.values():
            for parent, items in doc['navigation'].items():
                deep = self.page('/details/' + parent + '/')
                nav = deep.select_one('#razdely')
                actual = {a['href'] for a in nav.select('a[href]')}
                for item in items:
                    with self.subTest(parent=parent, href=item['href']):
                        self.assertIn(item['href'], actual)
                        self.assertNotIn('/karta/', item['href'])
                        self.assertIsNotNone(self.page(item['href']).select_one('.range-grid'))
                arguments = deep.select_one('.arguments')
                if arguments:
                    descendants = list(deep.descendants)
                    self.assertLess(descendants.index(nav), descendants.index(arguments))

    def test_single_frame_and_contact(self):
        reference = str(self.page('/').select_one('.contact'))
        for p in self.records:
            for route in ('/' + p['slug'] + '/', '/details/' + p['slug'] + '/'):
                with self.subTest(route=route):
                    doc = self.page(route)
                    self.assertEqual(str(doc.select_one('.contact')), reference)
                    self.assertEqual(len(doc.select('.site-footer')), 1)
                    self.assertEqual(len(doc.select('link[rel="stylesheet"]')), 1)
            deep = self.page('/details/' + p['slug'] + '/')
            self.assertEqual(deep.select_one('.wordmark').get_text(strip=True), 'ONTOS.RENT')
            self.assertEqual(deep.select_one('.meta a')['href'], '/')

    def test_new_layers_preserve_compiler_and_style(self):
        for doc in self.documents.values():
            self.assertNotIn('navigation_replace', doc)
            self.assertTrue(all('mode' not in p for p in doc['pages']))
        for path, digest in {
            'assets/canon.css': '04fd0f6c6ff73b23eb9676765fe3d94d7921e9b83800d920615146799ea8e12f',
            'scripts/site_core.py': '52692fae95ac56ce5c93328a0a4c3f7eb933ade9c66a6fbec9e9245cde1a9a26',
        }.items():
            self.assertEqual(sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)

    def test_important_variant_distinctions_remain_explicit(self):
        lookup = {p['slug']: p for p in self.records}
        markers = {
            'klarinet-in-es': ['рычаг', 'строя Es'],
            'bassetgorn': ['строй F', 'бассет-кларнета'],
            'goboy-damur': ['строя A', 'строя F'],
            'tsimbaly': ['педалью', 'палочки'],
            'yamaha-yfl372-v-arendu': ['372H', 'до-колену'],
            'yamaha-ycl450-v-arendu': ['450M', 'ABS'],
            'yamaha-yob241-v-arendu': ['си-бемоль', 'Нижняя'],
            'yamaha-yfg812-v-arendu': ['812C', 'соединением'],
            'yamaha-ytr4335gii-v-arendu': ['4335GSII', 'раструб'],
            'yamaha-ysl448g-v-arendu': ['13,89', '13,34', 'SL-48L'],
        }
        for slug, words in markers.items():
            p = lookup[slug]
            content = ' '.join(p['intro'] + [s for b in p['blocks'] for s in b['paragraphs']])
            for word in words:
                self.assertIn(word, content, (slug, word))


if __name__ == '__main__':
    unittest.main()
