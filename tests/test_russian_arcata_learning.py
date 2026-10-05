"""Russian Arcata learning brand and model routes."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

SLUGS={'smychkovye-arcata','arcata-gasparo-v-arendu','arcata-giovanni-v-arendu'}

class RussianArcataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz61-russian-arcata-learning.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/russian-arcata-learning-evidence.json',{})
        cls.temp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.temp.name)
        core.build(ROOT,cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self,slug,deep=False):
        return core.soup((self.output/('details' if deep else '')/slug/'index.html').read_text())

    def test_inventory_and_routes(self):
        result=inventory.inspect(ROOT)
        self.assertEqual(result['errors'],[])
        self.assertEqual(result['subjects'],1090)
        self.assertEqual({p['slug'] for p in self.doc['pages']},SLUGS)
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_arcata_is_bowed_child_brand(self):
        brand=self.page('smychkovye-arcata',True)
        self.assertEqual(brand.select_one('.site-footer a')['href'],'/details/smychkovye/')
        links={a['href'] for a in brand.select('#razdely a[href]')}
        self.assertIn('/arcata-gasparo-v-arendu/',links)
        self.assertIn('/arcata-giovanni-v-arendu/',links)
        root={a['href'] for a in self.page('',True).select('#razdely a[href]')}
        self.assertNotIn('/smychkovye-arcata/',root)

    def test_tier_and_size_are_not_collapsed(self):
        gas=next(p for p in self.doc['pages'] if p['slug']=='arcata-gasparo-v-arendu')
        gio=next(p for p in self.doc['pages'] if p['slug']=='arcata-giovanni-v-arendu')
        self.assertIn('ученичес',str(gas).casefold())
        self.assertIn('студенчес',str(gio).casefold())
        self.assertIn('1/4',str(gas))
        self.assertIn('3/4',str(gio))
        self.assertIn('4/4',str(gio))

    def test_evidence_is_school_use_not_national_ranking(self):
        self.assertEqual(self.ledger['new_subjects'],3)
        kinds={s['kind'] for s in self.ledger['sources'].values()}
        self.assertIn('supplier_case_report',kinds)
        self.assertIn('procurement_aggregator',kinds)
        for r in self.ledger['records']:
            self.assertEqual(r['availability'],'unconfirmed')
        text=' '.join(self.page(s,True).get_text(' ',strip=True) for s in SLUGS)
        self.assertNotIn('обязательный стандарт',text.casefold())
        self.assertNotIn('лучшая скрипка россии',text.casefold())

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
          'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
