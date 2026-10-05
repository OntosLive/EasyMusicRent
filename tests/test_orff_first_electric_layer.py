"""Regression coverage for Orff, first-electric, beginner acoustic/drums and Russian piano setup."""
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
    'zz53-orff-and-first-electric-learning.json',
    'zz54-russian-piano-study-setup.json',
    'zz55-early-orff-learning.json',
    'zz56-beginner-acoustic-banjo-drums-amps.json',
    'zz57-student-wind-alternatives.json',
    'zz58-student-flute-euphonium-ergonomics.json',
    'zz59-student-tenor-sax-alternative.json',
)

class OrffFirstElectricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = [core.read_json(ROOT/'content/sections'/name,{}) for name in BATCHES]
        cls.new = [p for d in cls.docs for p in d['pages'] if p.get('mode') != 'enrich']
        cls.enrich = [p for d in cls.docs for p in d['pages'] if p.get('mode') == 'enrich']
        cls.ledger = core.read_json(ROOT/'docs/research/orff-first-electric-evidence.json',{})
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name)
        cls.report = core.build(ROOT, cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self, slug, deep=False):
        return core.soup((self.output/('details' if deep else '')/slug/'index.html').read_text())

    def test_inventory_and_counts(self):
        result = inventory.inspect(ROOT)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['subjects'],1138)
        self.assertEqual(len(self.new), 28)
        self.assertEqual(len({p['slug'] for p in self.new}), 28)
        self.assertEqual(len(self.enrich), 7)
        for p in self.new:
            self.assertEqual(sum(x['slug']==p['slug'] for x in result['pages']),1,p['slug'])

    def test_new_page_pairs_and_editorial_contract(self):
        for p in self.new:
            with self.subTest(slug=p['slug']):
                entry, deep = self.page(p['slug']), self.page(p['slug'],True)
                self.assertEqual(core.text(entry.h1),p['search_title'])
                self.assertEqual(core.text(deep.h1),p['editorial_title'])
                self.assertIsNone(re.search(r'аренд|прокат|напрокат',p['editorial_title'],re.I))
                self.assertIsNone(entry.find('meta',attrs={'name':'robots'}))
                self.assertIn('noindex',deep.find('meta',attrs={'name':'robots'})['content'])
                self.assertEqual(len(entry.select('.contact-block')),1)
                self.assertEqual(len(deep.select('.contact-block')),1)

    def test_orff_is_child_category_not_new_root_family(self):
        orff = self.page('orf-instrumenty-dlya-obucheniya',True)
        self.assertEqual(orff.select_one('.site-footer a')['href'],'/details/udarnye/')
        links={a['href'] for a in orff.select('#razdely a[href]')}
        for href in (
            '/sonor-primary-sxp11-v-arendu/',
            '/studio49-seriya1000-v-arendu/',
            '/sonor-first-beat-v-arendu/',
            '/studio49-easycussion500-v-arendu/',
            '/sonor-global-beat-v-arendu/',
            '/orf-instrument-s-podpisannymi-notami/',
            '/orf-instrument-s-cvetovoy-kodirovkoy/',
        ):
            self.assertIn(href,links)
        root={a['href'] for a in self.page('',True).select('#razdely a[href]')}
        self.assertNotIn('/orf-instrumenty-dlya-obucheniya/',root)

    def test_beginner_routes_preserve_distinct_functions(self):
        texts={p['slug']:json.dumps(p,ensure_ascii=False) for p in self.new}
        self.assertIn('SSS',texts['squier-affinity-stratocaster-v-arendu'])
        self.assertIn('P/J',texts['yamaha-trbx174-v-arendu'])
        self.assertIn('BB234',texts['yamaha-bb234-v-arendu'])
        self.assertIn('color',texts['sonor-first-beat-v-arendu'].casefold())
        self.assertIn('пентатони',texts['studio49-easycussion500-v-arendu'].casefold())
        self.assertIn('3/4',texts['akusticheskaya-gitara-po-razmeru-uchenika'])
        self.assertIn('beaterless',texts['roland-td02k-v-arendu'])
        self.assertIn('10',texts['yamaha-dtx402k-v-arendu'])

    def test_enrichments_keep_existing_titles_and_parents(self):
        for p in self.enrich:
            self.assertNotIn('search_title',p)
            self.assertNotIn('editorial_title',p)
            self.assertNotIn('parent',p)
            self.assertNotIn('intro',p)
            self.assertNotIn('blocks',p)
            self.assertTrue(p.get('append_intro'))
        self.assertEqual(core.text(self.page('yamaha-pac112v-v-arendu',True).h1),
                         'Pacifica PAC112V: выбрать несколько рабочих звуков для своей программы')
        self.assertEqual(core.text(self.page('yamaha-fg800-v-arendu',True).h1),
                         'Yamaha FG800: услышать аккомпанемент рядом со своим голосом')

    def test_evidence_scope_is_explicit(self):
        self.assertEqual(self.ledger['expected_new_subjects'],28)
        self.assertEqual(len(self.ledger['records']),35)
        self.assertEqual(self.ledger['sources']['deering_teachers']['kind'],'manufacturer_teacher_survey')
        self.assertEqual(self.ledger['sources']['gorodische']['kind'],'school_inventory')
        self.assertEqual(self.ledger['sources']['pianino_ru']['kind'],'specialist_editorial_commercial')
        for source in self.ledger['sources'].values():
            self.assertEqual(urlsplit(source['url']).scheme,'https')
            self.assertTrue(source['kind'] and source['scope'])
        for record in self.ledger['records']:
            self.assertTrue(record['source_ids'])
            for sid in record['source_ids']:
                self.assertIn(sid,self.ledger['sources'])

    def test_quality_routes_are_live(self):
        quality={a['href'] for a in self.page('instrument-po-trebovaniyam-k-kachestvu',True).select('#razdely a[href]')}
        for href in (
            '/orf-instrument-s-podpisannymi-notami/',
            '/orf-instrument-s-cvetovoy-kodirovkoy/',
            '/bas-gitara-bez-drebezga-i-s-tochnoy-intonatsiey/',
            '/cifrovoe-pianino-na-ustoychivoy-stoyke/',
            '/akusticheskaya-gitara-po-razmeru-uchenika/',
        ):
            self.assertIn(href,quality)

    def test_compiler_and_css_remain_unchanged(self):
        expected={
            'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
            'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__ == '__main__':
    unittest.main()
