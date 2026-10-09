"""Content contracts for model-specific piano, electric strings and repertoire.

Tests preserve the established UI and existing documents. They do not establish
inventory, demand, rankings or complete semantic uniqueness of any request.
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
    'zz01-home-piano-models.json': 8,
    'zz02-acoustic-piano-models.json': 8,
    'zz03-electric-bowed-models.json': 8,
    'zz04-keyboard-repertoire-landings.json': 8,
}
COMMERCIAL = re.compile(r'\b(?:аренд\w*|прокат\w*|напрокат)\b', re.I)


class PianoBowedRepertoireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temporary.name)
        cls.report = core.build(ROOT, cls.output)
        cls.documents = {name: core.read_json(ROOT / 'content/sections' / name, {})
                         for name in BATCHES}
        cls.records = [p for d in cls.documents.values() for p in d['pages']]
        cls.lookup = {p['slug']: p for p in cls.records}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @lru_cache(maxsize=None)
    def page(self, url):
        return core.soup((self.output / url.strip('/') / 'index.html').read_text(encoding='utf-8'))

    def body_text(self, slug):
        return core.text(self.page('/details/' + slug + '/').select_one('main'))

    def test_all_four_layers_and_unique_requests(self):
        for name, count in BATCHES.items():
            self.assertEqual(len(self.documents[name]['pages']), count, name)
        self.assertEqual(len(self.lookup), 32)
        self.assertEqual(len({p['search_title'] for p in self.records}), 32)
        all_titles = [p['entry_title'].casefold() for p in self.report['pages']]
        self.assertEqual(len(all_titles), len(set(all_titles)))

    def test_search_and_editorial_contracts(self):
        for p in self.records:
            with self.subTest(slug=p['slug']):
                entry = self.page('/' + p['slug'] + '/')
                deep = self.page('/details/' + p['slug'] + '/')
                self.assertEqual(core.text(entry.h1), p['search_title'])
                self.assertEqual(core.text(deep.h1), p['editorial_title'])
                self.assertIsNotNone(COMMERCIAL.search(p['search_title']))
                self.assertIsNone(COMMERCIAL.search(p['editorial_title']))
                self.assertIsNone(entry.find('meta', attrs={'name': 'robots'}))
                self.assertNotIn('noindex', core.meta(deep, 'robots').casefold())
                self.assertEqual(entry.select_one('.site-footer a')['href'], '/details/' + p['slug'] + '/')
                self.assertEqual(deep.select_one('.site-footer a')['href'], '/details/' + p['parent'] + '/')

    def test_authored_copy_sources_and_no_exact_paragraph_repeats(self):
        seen = {}
        for p in self.records:
            with self.subTest(slug=p['slug']):
                self.assertEqual(len(p['blocks']), 3)
                self.assertEqual([b['label'][:2] for b in p['blocks']], ['01', '02', '03'])
                self.assertTrue(p['description'] and p['intro'] and p['quote'] and p['sources'])
                self.assertTrue(p['quote'].endswith('?'))
                # An empty-record check only, not a target for textual padding.
                self.assertGreater(len(self.body_text(p['slug']).split()), 150)
                for source in p['sources']:
                    self.assertEqual(urlsplit(source['url']).scheme, 'https')
                    self.assertTrue(source['title'])
                for b in p['blocks']:
                    self.assertTrue(b['title'])
                    for paragraph in b['paragraphs']:
                        normalized = re.sub(r'\s+', ' ', core.text(core.soup(paragraph))).casefold()
                        self.assertNotIn(normalized, seen, (p['slug'], seen.get(normalized)))
                        seen[normalized] = p['slug']

    def test_declared_routes_are_live_before_block_01(self):
        for document in self.documents.values():
            for parent, links in document['navigation'].items():
                deep = self.page('/details/' + parent + '/')
                nav = deep.select_one('#razdely')
                self.assertIsNotNone(nav, parent)
                actual = {a['href'] for a in nav.select('a[href]')}
                for link in links:
                    self.assertIn(link['href'], actual, parent)
                    self.assertIsNone(self.page(link['href']).find('meta', attrs={'http-equiv': 'refresh'}))
                blocks = deep.select_one('.arguments')
                if blocks:
                    order = list(deep.descendants)
                    self.assertLess(order.index(nav), order.index(blocks), parent)

    def test_one_frame_contact_and_unchanged_compiler(self):
        reference = str(self.page('/').select_one('.contact'))
        for p in self.records:
            for url in ('/' + p['slug'] + '/', '/details/' + p['slug'] + '/'):
                doc = self.page(url)
                self.assertEqual(str(doc.select_one('.contact')), reference, url)
                self.assertEqual(len(doc.select('.site-footer')), 1)
                self.assertEqual(len(doc.select('link[rel="stylesheet"]')), 1)
            deep = self.page('/details/' + p['slug'] + '/')
            self.assertEqual(deep.select_one('.wordmark').get_text(strip=True), 'ONTOS.RENT')
            self.assertEqual(deep.select_one('.meta a')['href'], '/')
        for path, expected in {
            'assets/canon.css': '04fd0f6c6ff73b23eb9676765fe3d94d7921e9b83800d920615146799ea8e12f',
            'scripts/site_core.py': '01a4af94326065d30cfddfaf7974c7763ba3a9f81911add3ca84052caea36256',
        }.items():
            self.assertEqual(sha256((ROOT / path).read_bytes()).hexdigest(), expected)
        for doc in self.documents.values():
            self.assertNotIn('navigation_replace', doc)
            self.assertTrue(all('mode' not in p for p in doc['pages']))

    def test_electronics_and_accessories_are_not_conflated(self):
        markers = {
            'casio-cdps110-v-arendu': ['SP-3', 'Отдельного разъёма'],
            'casio-cdps160-v-arendu': ['SP-34', 'дополнительные принадлежности'],
            'kawai-kdp120-v-arendu': ['Bluetooth MIDI', 'не обещание Bluetooth-аудио'],
            'yamaha-ysv104-v-arendu': ['собственный блок', 'других моделей'],
            'yamaha-yev104-v-arendu': ['пассивный', 'не встроенный усилитель'],
            'yamaha-yev105-v-arendu': ['нижняя струна до', 'акустическим альтом'],
            'yamaha-sv250-v-arendu': ['XLR', 'независимой регулировкой'],
            'yamaha-slb300-v-arendu': ['1040', 'отдельного выхода Phones нет', 'семплов'],
        }
        for slug, words in markers.items():
            for word in words:
                self.assertIn(word, self.body_text(slug), (slug, word))

    def test_model_and_repertoire_distinctions_remain_explicit(self):
        markers = {
            'yamaha-b1-v-arendu': ['Muffler', 'SILENT'],
            'yamaha-b3-v-arendu': ['b3 и U1', 'разным сериям'],
            'yamaha-c3x-v-arendu': ['C3 и C3X', 'одним обозначением'],
            'yamaha-c7x-v-arendu': ['227', 'CFX'],
            'pianino-dlya-igry-v-chetyre-ruki': ['один инструмент', 'Duet'],
            'dva-royalya-dlya-fortepiannogo-dueta': ['два самостоятельных', 'другой редакции'],
            'pianino-s-pedalyu-sostenuto': ['Полупедаль', 'не равна sostenuto'],
            'klavishnye-s-mikrotonalnoy-nastroykoy': ['монофоническим', 'MIDI Tuning Standard'],
            'pianino-dlya-videozayavki': ['именно этого отбора', 'не подтверждает соответствие'],
        }
        for slug, words in markers.items():
            for word in words:
                self.assertIn(word, self.body_text(slug), (slug, word))

    def test_task_pages_keep_direct_instrument_choices(self):
        for p in self.documents['zz04-keyboard-repertoire-landings.json']['pages']:
            deep = self.page('/details/' + p['slug'] + '/')
            self.assertGreaterEqual(len(deep.select('#razdely a[href]')), 2, p['slug'])
            for a in deep.select('#razdely a[href]'):
                self.assertNotIn('/karta/', a['href'])
                self.assertTrue(self.page(a['href']).select_one('.range-grid'))


if __name__ == '__main__':
    unittest.main()
