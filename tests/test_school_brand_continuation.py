"""Preserve source scope and existing routes while extending school guidance."""
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
from source_policy import public_sources

BATCHES = (
    'zz50-russian-bayan-school-context.json',
    'zz51-school-string-brand-paths.json',
    'zz52-practice-quality-and-exam-context.json',
)

class SchoolBrandContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = [core.read_json(ROOT/'content/sections'/name, {}) for name in BATCHES]
        cls.new = [r for d in cls.docs for r in d['pages'] if r.get('mode') != 'enrich']
        cls.enrich = [r for d in cls.docs for r in d['pages'] if r.get('mode') == 'enrich']
        cls.ledger = core.read_json(ROOT/'docs/research/school-brand-quality-continuation.json', {})
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name)
        cls.report = core.build(ROOT, cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self, slug, deep=False):
        return core.soup((self.output/('details' if deep else '')/slug/'index.html').read_text())

    def test_inventory_new_subjects_and_enrichments_are_distinct(self):
        result = inventory.inspect(ROOT)
        self.assertEqual(result['errors'], [])
        slugs = [p['slug'] for p in self.new]
        self.assertEqual(len(slugs), 12)
        self.assertEqual(len(set(slugs)), 12)
        self.assertEqual(len(self.enrich), 3)
        for slug in slugs:
            self.assertEqual(sum(p['slug'] == slug for p in result['pages']), 1)
        self.assertEqual({p['slug'] for p in self.enrich},
                         {'bayan-s-vybornym-basom', 'violonchel-knilling', 'pianino-dlya-videozayavki'})

    def test_page_pair_and_contact_contracts(self):
        for p in self.new:
            with self.subTest(slug=p['slug']):
                entry, deep = self.page(p['slug']), self.page(p['slug'], True)
                self.assertEqual(core.text(entry.h1), p['search_title'])
                self.assertEqual(core.text(deep.h1), p['editorial_title'])
                self.assertIsNone(re.search(r'аренд|прокат|напрокат', p['editorial_title'], re.I))
                self.assertIsNone(entry.find('meta', attrs={'name':'robots'}))
                self.assertNotIn('noindex', core.meta(deep, 'robots').casefold())
                self.assertEqual(len(entry.select('.contact-block')), 1)
                self.assertEqual(len(deep.select('.contact-block')), 1)
                self.assertEqual(deep.select_one('.site-footer a')['href'], '/details/'+p['parent']+'/')

    def test_new_copy_has_specific_blocks_and_no_repeated_paragraphs(self):
        seen = set()
        for p in self.new:
            self.assertEqual(len(p['blocks']), 3)
            self.assertEqual([b['label'][:2] for b in p['blocks']], ['01','02','03'])
            self.assertTrue(p['quote'] and p['sources'])
            self.assertNotIn('—', json.dumps(p, ensure_ascii=False))
            for b in p['blocks']:
                self.assertTrue(b['title'])
                for paragraph in b['paragraphs']:
                    norm = re.sub(r'\s+', ' ', core.text(core.soup(paragraph))).casefold()
                    self.assertNotIn(norm, seen)
                    seen.add(norm)

    def test_navigation_is_live_and_no_root_family_is_added(self):
        for d in self.docs:
            self.assertNotIn('navigation_replace', d)
            self.assertNotIn('', d['navigation'])
            for parent, links in d['navigation'].items():
                actual = {a['href'] for a in self.page(parent, True).select('#razdely a[href]')}
                for link in links:
                    self.assertIn(link['href'], actual, (parent, link))
        root_links = {a['href'] for a in self.page('', True).select('#razdely a[href]')}
        self.assertNotIn('/bayany-yupiter/', root_links)
        self.assertNotIn('/smychkovye-knilling/', root_links)
        for slug in ('bayan-yupiter-2d-v-arendu','shen-sb80-v-arendu','shen-sb150-v-arendu'):
            self.assertTrue(self.page(slug).find('h1'))

    def test_brand_model_and_construction_distinctions_are_explicit(self):
        pages = {p['slug']: json.dumps(p, ensure_ascii=False) for p in self.new}
        self.assertIn('Jupiter', pages['bayany-yupiter'])
        self.assertIn('духовых', pages['bayany-yupiter'])
        self.assertIn('четырьмя рядами', pages['bayan-yupiter-2d-v-arendu'])
        self.assertIn('без регистров', pages['bayan-yupiter-2d-v-arendu'])
        self.assertIn('Eastman VB80', pages['shen-sb80-v-arendu'])
        self.assertIn('электроники', pages['shen-sb150-v-arendu'])
        self.assertIn('ламинированными', pages['smychkovye-samuel-shen'])
        self.assertIn('2025', pages['knilling-bucharest-skripka-v-arendu'])

    def test_evidence_retains_dates_scope_and_unconfirmed_availability(self):
        sources = self.ledger['sources']
        self.assertEqual(len(self.ledger['records']), 15)
        self.assertEqual(sources['beltsville']['kind'], 'school_recommendation')
        self.assertEqual(sources['beltsville']['model_recommendations'], [])
        self.assertEqual(sources['kazan_delivery']['kind'], 'supplier_case_report')
        self.assertEqual(sources['kazan_delivery']['event_month'], '2024-03')
        self.assertEqual(sources['trinity_piano']['published_on'], '2023-04')
        for p in self.ledger['records']:
            self.assertEqual(p['availability'], 'unconfirmed')
            self.assertEqual(p['exercise_status'], 'editorial_suggestion')
            self.assertTrue(p['source_ids'])
            for key in p['source_ids']:
                self.assertIn(key, sources)
        for source in sources.values():
            self.assertEqual(urlsplit(source['url']).scheme, 'https')
            self.assertTrue(source['kind'] and source['scope'] and source['access'])

    def test_enrichment_preserves_all_original_text_and_headings(self):
        legacy = core.read_legacy(ROOT, core.read_json(ROOT/'content/legacy-metadata.json', {}))
        old = {'violonchel-knilling': legacy['violonchel-knilling']}
        for filename, slug in [('70-bellows-reeds.json','bayan-s-vybornym-basom'),
                               ('zz04-keyboard-repertoire-landings.json','pianino-dlya-videozayavki')]:
            doc = core.read_json(ROOT/'content/sections'/filename,{})
            old[slug] = next(p for p in doc['pages'] if p['slug']==slug)
        merged = core.read_legacy(ROOT, core.read_json(ROOT/'content/legacy-metadata.json', {}))
        core.merge_records(ROOT, merged)
        for record in self.enrich:
            self.assertTrue(record['append_intro'])
            self.assertFalse({'intro','blocks','search_title','editorial_title','parent'} & record.keys())
            slug=record['slug']; original=old[slug]
            get = original.get if isinstance(original,dict) else lambda key: getattr(original,key)
            page=self.page(slug,True); text=page.get_text(' ',strip=True)
            self.assertEqual(core.text(page.h1), get('editorial_title'))
            for paragraph in get('intro'):
                self.assertIn(core.text(core.soup(paragraph)), text)
            for block in get('blocks'):
                for paragraph in block['paragraphs']:
                    self.assertIn(core.text(core.soup(paragraph)), text)
            sources = merged[slug].sources
            self.assertEqual(sources, record['sources'])
            for src in get('sources'):
                self.assertIn(src, sources)
            actual = [(a['href'], core.text(a)) for a in page.select('.sources a[href]')]
            self.assertEqual(actual, [(s['url'], s['title']) for s in public_sources(sources)])

    def test_exam_scope_is_dated_and_not_a_universal_piano_rule(self):
        text=self.page('pianino-dlya-videozayavki',True).get_text(' ',strip=True)
        for required in ('апреля 2023', 'ATCL', 'LTCL', 'акустический', 'своей экзаменационной сессии'):
            self.assertIn(required,text)
        self.assertIn('Универсальные 88 клавиш',text)
        self.assertNotIn('Trinity рекомендует Kawai',text)

    def test_compiler_styles_and_prior_tests_are_unchanged(self):
        expected = {
            'scripts/site_core.py':'01a4af94326065d30cfddfaf7974c7763ba3a9f81911add3ca84052caea36256',
            'assets/canon.css':'04fd0f6c6ff73b23eb9676765fe3d94d7921e9b83800d920615146799ea8e12f',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)
        self.assertIn('self.assertEqual(len(slugs), 94)',(ROOT/'tests/test_education_quality.py').read_text())
        self.assertNotIn('zz50-',(ROOT/'tests/test_education_quality.py').read_text())

if __name__ == '__main__':
    unittest.main()
