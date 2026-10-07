"""Regression coverage for named learning instruments and quality-led entrances."""
import json
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
import content_inventory as inventory

BATCHES = (
    'zz38-rider-guitars-and-di.json',
    'zz39-bowed-brand-education.json',
    'zz40-learning-models-and-levels.json',
    'zz41-quality-request-entrances.json',
    'zz42-education-quality-navigation.json',
    'zz43-golden-learning-standards-2.json',
    'zz44-golden-learning-standards-3.json',
    'zz45-quality-entrances-2.json',
    'zz46-international-student-wind-standards.json',
    'zz47-learning-harps-keys-recorder-mandolin.json',
)
HUBS = ('instrument-po-rekomendatsii-prepodavatelya',
        'instrument-po-trebovaniyam-k-kachestvu')


class EducationQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = [json.loads((ROOT/'content/sections'/p).read_text()) for p in BATCHES]
        cls.records = [p for doc in cls.docs for p in doc['pages']]
        cls.coverage = json.loads((ROOT/'docs/research/education-quality-coverage.json').read_text())
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name)
        cls.report = core.build(ROOT, cls.output)
        cls.current = {p['slug']: p for p in cls.report['pages']}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self, slug, deep=False):
        route = ('details/' if deep else '') + slug
        return core.soup((self.output/route/'index.html').read_text())

    def test_new_subjects_have_one_owner(self):
        result = inventory.inspect(ROOT)
        self.assertEqual(result['errors'], [])
        slugs = [p['slug'] for p in self.records]
        self.assertEqual(len(slugs), 94)
        self.assertEqual(len(set(slugs)), len(slugs))
        for slug in slugs:
            self.assertEqual(sum(p['slug'] == slug for p in result['pages']), 1, slug)

    def test_request_and_editorial_pairs_keep_distinct_contracts(self):
        for record in self.records:
            with self.subTest(slug=record['slug']):
                entry = self.page(record['slug'])
                deep = self.page(record['slug'], True)
                # Later reviewed layers can refine wording while preserving the pair.
                current = self.current[record['slug']]
                self.assertEqual(core.text(entry.h1), current['entry_title'])
                self.assertEqual(core.text(deep.h1), current['editorial_title'])
                self.assertNotEqual(current['entry_title'], current['editorial_title'])
                self.assertIsNone(re.search(r'аренд|прокат|напрокат', current['editorial_title'], re.I))
                self.assertNotIn('noindex', core.meta(deep, 'robots').casefold())
                self.assertIsNone(entry.find('meta', attrs={'name':'robots'}))
                self.assertEqual(len(entry.select('.contact-block')), 1)
                self.assertEqual(len(deep.select('.contact-block')), 1)

    def test_every_family_has_live_education_and_quality_routes(self):
        families = self.coverage['families']
        self.assertEqual(len(families), 13)
        self.assertEqual(len({f['family'] for f in families}), 13)
        for family in families:
            deep = self.page(family['family'], True)
            routes = {a['href'] for a in deep.select('#razdely a[href]')}
            for hub in HUBS:
                self.assertIn('/'+hub+'/', routes)
            for slug in family['model_brand_entries'] + family['quality_entries']:
                self.assertTrue((self.output/slug/'index.html').exists(), slug)
        root = self.page('', True)
        self.assertTrue(all('/'+hub+'/' not in {a['href'] for a in root.select('#razdely a[href]')}
                            for hub in HUBS))

    def test_evidence_records_retain_scope_and_unconfirmed_availability(self):
        ledger = self.coverage['sources']
        self.assertTrue({'RU','US','GB','DE','CZ','ES','JP'} <=
                        {s['country_of_evidence'] for s in ledger.values()})
        for source in ledger.values():
            self.assertEqual(urlsplit(source['url']).scheme, 'https')
            self.assertTrue(source['scope'] and source['kind'])
        self.assertEqual(ledger['royal']['kind'], 'school_recommendation')
        self.assertEqual(ledger['dshi']['kind'], 'school_inventory')
        for record in self.coverage['records']:
            self.assertEqual(record['availability'], 'unconfirmed')
            self.assertTrue(record['sources'])
            for key in record['sources']:
                self.assertIn(key, ledger)

    def test_brand_names_and_homonyms_are_not_collapsed(self):
        pages = {p['slug']: p for p in self.records}
        for slug in ('smychkovye-strunal','kontrabas-rubner','smychkovye-musima',
                     'smychkovye-cremona-luby','smychkovye-cremona-saga'):
            self.assertIn(slug, pages)
        luby = json.dumps(pages['smychkovye-cremona-luby'], ensure_ascii=False)
        saga = json.dumps(pages['smychkovye-cremona-saga'], ensure_ascii=False)
        self.assertIn('Strunal', luby)
        self.assertIn('Saga', saga)
        self.assertNotEqual(pages['smychkovye-cremona-luby']['search_title'],
                            pages['smychkovye-cremona-saga']['search_title'])
        self.assertIn('механик', json.dumps(pages['kontrabas-rubner'], ensure_ascii=False))

    def test_quality_pages_have_specific_checks_and_no_exact_paragraph_copies(self):
        seen = set()
        for record in self.records:
            self.assertEqual(len(record['blocks']), 3)
            self.assertTrue(record['sources'] and record['quote'])
            for block in record['blocks']:
                for paragraph in block['paragraphs']:
                    normalized = re.sub(r'\s+', ' ', core.text(core.soup(paragraph))).casefold()
                    self.assertNotIn(normalized, seen, record['slug'])
                    seen.add(normalized)
        self.assertEqual(sum(p['role'] == 'quality' for p in self.coverage['records']), 25)

    def test_old_cello_brand_pages_and_bass_quality_routes_survive(self):
        for slug in ('violonchel-strunal','violonchel-stentor','violonchel-eastman',
                     'violonchel-gewa','kontrabas-s-nizkoy-vysotoy-strun',
                     'udobnaya-violonchel','alt-dlya-nebolshoy-ruki'):
            self.assertTrue((self.output/slug/'index.html').exists(), slug)
            self.assertTrue((self.output/'details'/slug/'index.html').exists(), slug)

    def test_layout_compiler_and_stylesheet_are_unchanged(self):
        expected = {
            'assets/canon.css':'699834b7f5983c453e7d8f5703fb56ebb30cf461896805926b7b68993e6338af',
            'scripts/site_core.py':'52692fae95ac56ce5c93328a0a4c3f7eb933ade9c66a6fbec9e9245cde1a9a26',
        }
        for path, digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
