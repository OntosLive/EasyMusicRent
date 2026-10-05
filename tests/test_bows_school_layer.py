"""Regression coverage for the bow branch and source-bounded school evidence."""
import json
import re
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import site_core as core
import content_inventory as inventory

BATCHES = ('zz48-bows-learning-and-quality.json',
           'zz49-school-bowed-and-piano-evidence.json')


class BowsSchoolLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = [json.loads((ROOT/'content/sections'/name).read_text())
                    for name in BATCHES]
        cls.records = [p for doc in cls.docs for p in doc['pages']
                       if p.get('mode') != 'enrich']
        cls.ledger = json.loads((ROOT/'docs/research/bows-and-school-evidence.json').read_text())
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name)
        cls.report = core.build(ROOT, cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self, slug, deep=False):
        route = ('details/' if deep else '') + slug
        return core.soup((self.output/route/'index.html').read_text())

    def test_all_new_subjects_have_exactly_one_owner(self):
        report = inventory.inspect(ROOT)
        self.assertEqual(report['errors'], [])
        slugs = [p['slug'] for p in self.records]
        self.assertEqual(len(slugs), 19)
        self.assertEqual(len(set(slugs)), 19)
        for slug in slugs:
            self.assertEqual(sum(r['slug'] == slug for r in report['pages']), 1, slug)

    def test_pairs_and_contacts_keep_existing_contracts(self):
        for p in self.records:
            with self.subTest(slug=p['slug']):
                entry, deep = self.page(p['slug']), self.page(p['slug'], True)
                self.assertEqual(core.text(entry.h1), p['search_title'])
                self.assertEqual(core.text(deep.h1), p['editorial_title'])
                self.assertIsNone(re.search(r'аренд|прокат|напрокат', p['editorial_title'], re.I))
                self.assertIsNone(entry.find('meta', attrs={'name':'robots'}))
                self.assertIn('noindex', deep.find('meta', attrs={'name':'robots'})['content'])
                self.assertEqual(len(entry.select('.contact-block')), 1)
                self.assertEqual(len(deep.select('.contact-block')), 1)
                self.assertEqual(deep.select_one('.site-footer a')['href'], '/details/'+p['parent']+'/')

    def test_bows_are_a_child_branch_with_all_declared_links(self):
        root_links = {a['href'] for a in self.page('', True).select('#razdely a[href]')}
        self.assertNotIn('/smychki/', root_links)
        self.assertIn('/usiliteli-backline/', root_links)
        for doc in self.docs:
            self.assertNotIn('navigation_replace', doc)
            for parent, links in doc['navigation'].items():
                actual = {a['href'] for a in self.page(parent, True).select('#razdely a[href]')}
                for link in links:
                    self.assertIn(link['href'], actual, (parent, link))
        for parent in ('skripka','alt','violonchel','kontrabas'):
            self.assertTrue(any('smychki/' in a['href'] for a in
                                self.page(parent, True).select('#razdely a[href]')))

    def test_authored_pages_keep_distinct_content(self):
        seen = set()
        for p in self.records:
            self.assertEqual(len(p['blocks']), 3)
            self.assertTrue(p['quote'] and p['sources'])
            for block in p['blocks']:
                self.assertTrue(block['title'])
                for text in block['paragraphs']:
                    normalized = re.sub(r'\s+', ' ', core.text(core.soup(text))).casefold()
                    self.assertNotIn(normalized, seen, p['slug'])
                    seen.add(normalized)

    def test_evidence_has_scope_and_never_confirms_stock(self):
        sources = self.ledger['sources']
        self.assertTrue({'RU','US','DE','GB','SG'} <=
                        {s['country_of_evidence'] for s in sources.values()})
        self.assertEqual(len(self.ledger['records']), 20)
        for record in self.ledger['records']:
            self.assertEqual(record['availability'], 'unconfirmed')
            self.assertEqual(record['exercise_status'], 'editorial_suggestion')
            self.assertTrue(record['source_ids'])
            for key in record['source_ids']:
                self.assertIn(key, sources)
        for source in sources.values():
            self.assertTrue(source['scope'] and source['kind'] and source['access'])
            self.assertEqual(urlsplit(source['url']).scheme, 'https')
        self.assertEqual(sources['school']['kind'], 'school_requirement')
        self.assertEqual(sources['school']['model_recommendations'], [])
        self.assertTrue(sources['school']['excluded_claim'])
        self.assertEqual(sources['lvl']['kind'], 'music_school_shop')

    def test_old_piano_quality_copy_is_preserved(self):
        doc = json.loads((ROOT/'content/sections/zz41-quality-request-entrances.json').read_text())
        old = next(p for p in doc['pages'] if p['slug'] == 'pianino-s-rovnoy-klaviaturoy')
        deep = self.page(old['slug'], True)
        text = deep.get_text(' ', strip=True)
        self.assertEqual(core.text(deep.h1), old['editorial_title'])
        for fragment in old['intro']:
            self.assertIn(core.text(core.soup(fragment)), text)
        for block in old['blocks']:
            for paragraph in block['paragraphs']:
                self.assertIn(core.text(core.soup(paragraph)), text)
        self.assertIn('Рубинштейна', text)
        self.assertTrue(any('rubinstein-school.ru' in a['href'] for a in deep.select('a[href]')))

    def test_models_and_components_are_not_conflated(self):
        lookup = {p['slug']:p for p in self.records}
        bass = json.dumps(lookup['eastman-vb80-v-arendu'], ensure_ascii=False)
        self.assertIn('Изготовитель контрабаса остаётся Eastman', bass)
        self.assertIn('Rubner', bass)
        self.assertFalse(any('prodigy' in s and 'kontrabas' in s for s in lookup))
        french = lookup['frantsuzskiy-smychok-dlya-kontrabasa']
        german = lookup['nemetskiy-smychok-dlya-kontrabasa']
        self.assertEqual(french['parent'], 'kontrabasovye-smychki')
        self.assertEqual(german['parent'], 'kontrabasovye-smychki')
        self.assertIn('страну', json.dumps(german, ensure_ascii=False))

    def test_compiler_css_and_previous_education_suite_remain_intact(self):
        expected = {
            'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
            'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
        }
        for path, digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(), digest)
        old = (ROOT/'tests/test_education_quality.py').read_text()
        self.assertIn('self.assertEqual(len(slugs), 94)', old)
        self.assertNotIn('zz48-', old)


if __name__ == '__main__':
    unittest.main()
