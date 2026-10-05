"""GEWA educational ladder stays source-bounded and non-normative."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

SLUGS={
 'smychkovye-gewa',
 'gewa-allegro-skripka-v-arendu',
 'gewa-ideale-skripka-v-arendu',
 'gewa-maestro1-skripka-v-arendu',
 'gewa-allegro-violonchel-v-arendu',
}

class GewaEducationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz70-gewa-education-family.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/gewa-education-evidence.json',{})
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
        self.assertEqual(result['subjects'],1138)
        self.assertEqual({p['slug'] for p in self.doc['pages']},SLUGS)
        enrich=[p for p in self.doc['pages'] if p.get('mode')=='enrich']
        self.assertEqual([p['slug'] for p in enrich],['gewa-ideale-skripka-v-arendu'])
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_gewa_is_child_brand_not_root_family(self):
        brand=self.page('smychkovye-gewa',True)
        self.assertEqual(brand.select_one('.site-footer a')['href'],'/details/smychkovye/')
        root={a['href'] for a in self.page('',True).select('#razdely a[href]')}
        self.assertNotIn('/smychkovye-gewa/',root)

    def test_size_and_tier_are_not_collapsed(self):
        allegro=next(p for p in self.doc['pages'] if p['slug']=='gewa-allegro-skripka-v-arendu')
        ideale=next(p for p in self.doc['pages'] if p['slug']=='gewa-ideale-skripka-v-arendu')
        maestro=next(p for p in self.doc['pages'] if p['slug']=='gewa-maestro1-skripka-v-arendu')
        self.assertIn('1/16',str(allegro))
        self.assertIn('1/4',str(ideale))
        self.assertIn('advanced',str(maestro).casefold())

    def test_manufacturer_taxonomy_is_bounded(self):
        text=' '.join(self.page(s,True).get_text(' ',strip=True) for s in SLUGS)
        self.assertNotIn('единый стандарт европы',text.casefold())
        self.assertNotIn('обязательная модель',text.casefold())
        self.assertEqual(self.ledger['sources']['strings_catalog']['kind'],'manufacturer_catalog')
        self.assertEqual(self.ledger['new_subjects'],4)
        ide=next(r for r in self.ledger['records'] if r['slug']=='gewa-ideale-skripka-v-arendu')
        self.assertEqual(ide.get('action'),'enrich')
        for record in self.ledger['records']:
            self.assertEqual(record['availability'],'unconfirmed')

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
          'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
