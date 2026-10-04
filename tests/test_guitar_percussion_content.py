"""Regression checks for guitar configurations and orchestral percussion.

These checks establish completeness and preserve routes. They do not substitute
for editorial review, source checking, or actual instrument availability.
"""
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

LAYERS = (
    '99b-guitar-configurations.json', '99c-bass-and-baritone-ukulele.json',
    '99d-orchestral-percussion.json', '99e-resonant-percussion.json',
)
EXPECTED = (
    {'dvenadtsatistrunnaya-gitara', 'bariton-gitara', 'rezonatornaya-gitara',
     'lap-stil-gitara', 'gitara-dlya-levshi'},
    {'pyatistrunnaya-bas-gitara', 'shestistrunnaya-bas-gitara',
     'korotkomensurnaya-bas-gitara', 'akusticheskaya-bas-gitara', 'ukulele-bariton'},
    {'bolshoy-orkestrovyy-baraban', 'orkestrovye-parnye-tarelki', 'podvesnaya-tarelka',
     'orkestrovyy-treugolnik', 'orkestrovyy-buben'},
    {'orkestrovye-kolokolchiki', 'krotali', 'tamtam', 'nastroennyy-gong', 'kovbell'},
)


class GuitarPercussionContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temporary.name)
        cls.report = core.build(ROOT, cls.output)
        cls.documents = [core.read_json(ROOT / 'content/sections' / name, {}) for name in LAYERS]
        cls.records = [record for document in cls.documents for record in document['pages']]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def page(self, route):
        return core.soup((self.output / route.strip('/') / 'index.html').read_text(encoding='utf-8'))

    def test_layer_membership_and_two_page_roles(self):
        for document, expected in zip(self.documents, EXPECTED):
            self.assertEqual({p['slug'] for p in document['pages']}, expected)
        commercial = re.compile(r'\b(?:аренд\w*|прокат\w*|напрокат)\b', re.I)
        for record in self.records:
            with self.subTest(slug=record['slug']):
                entry = self.page('/' + record['slug'] + '/')
                deep = self.page('/details/' + record['slug'] + '/')
                self.assertEqual(core.text(entry.h1), record['search_title'])
                self.assertEqual(core.text(deep.h1), record['editorial_title'])
                self.assertIsNotNone(commercial.search(record['search_title']))
                self.assertIsNone(commercial.search(record['editorial_title']))
                self.assertEqual(entry.select_one('.site-footer a')['href'], '/details/' + record['slug'] + '/')
                self.assertIn('noindex', deep.find('meta', attrs={'name': 'robots'})['content'])

    def test_each_article_has_complete_distinct_content_and_sources(self):
        paragraphs = set()
        for record in self.records:
            with self.subTest(slug=record['slug']):
                self.assertEqual(len(record['blocks']), 3)
                self.assertEqual([x['label'][:2] for x in record['blocks']], ['01', '02', '03'])
                # Introduction length follows the subject, not a padding quota.
                self.assertTrue(core.text(core.soup(' '.join(record['intro']))))
                deep = self.page('/details/' + record['slug'] + '/')
                self.assertGreater(len(core.text(deep.select_one('main')).split()), 180)
                self.assertTrue(record['sources'])
                for source in record['sources']:
                    self.assertEqual(urlsplit(source['url']).scheme, 'https')
                    self.assertTrue(source['title'])
                for block in record['blocks']:
                    self.assertTrue(block['title'])
                    for paragraph in block['paragraphs']:
                        normalized = re.sub(r'\s+', ' ', paragraph).strip().casefold()
                        self.assertNotIn(normalized, paragraphs, record['slug'])
                        paragraphs.add(normalized)

    def test_all_declared_navigation_resolves_to_request_page(self):
        for document in self.documents:
            for parent, links in document['navigation'].items():
                deep = self.page('/details/' + parent + '/')
                actual = {a['href'] for a in deep.select('#razdely a[href]')}
                for link in links:
                    with self.subTest(parent=parent, child=link['href']):
                        self.assertIn(link['href'], actual)
                        target = self.page(link['href'])
                        self.assertIsNotNone(target.select_one('.range-grid'))
                        self.assertIsNone(target.find('meta', attrs={'http-equiv': 'refresh'}))

    def test_new_subjects_have_parent_return_and_one_shared_contact(self):
        reference = str(self.page('/').select_one('.contact'))
        for record in self.records:
            for route in ('/' + record['slug'] + '/', '/details/' + record['slug'] + '/'):
                with self.subTest(route=route):
                    page = self.page(route)
                    self.assertEqual(str(page.select_one('.contact')), reference)
                    self.assertEqual(len(page.select('.site-footer')), 1)
            deep = self.page('/details/' + record['slug'] + '/')
            self.assertEqual(deep.select_one('.site-footer a')['href'], '/details/' + record['parent'] + '/')

    def test_this_layer_adds_content_without_replacing_earlier_records(self):
        for document in self.documents:
            self.assertNotIn('navigation_replace', document)
            self.assertTrue(all('mode' not in p for p in document['pages']))
        expected_hash = '0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54'
        self.assertEqual(sha256((ROOT / 'assets/canon.css').read_bytes()).hexdigest(), expected_hash)


if __name__ == '__main__':
    unittest.main()
