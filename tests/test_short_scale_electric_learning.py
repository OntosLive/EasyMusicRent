"""Short-scale electric guitar and bass learning routes."""
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
 'squier-mini-stratocaster-v-arendu',
 'ibanez-pgmm31-v-arendu',
 'elektrogitara-dlya-nebolshoy-ruki',
 'squier-mini-precision-bass-v-arendu',
 'ibanez-gsrm20-v-arendu',
 'bas-gitara-korotkoy-menzury-dlya-nebolshoy-ruki',
}

class ShortScaleElectricLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz74-short-scale-electric-learning.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/short-scale-electric-learning-evidence.json',{})
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
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_short_scale_geometry_is_explicit(self):
        mini=self.page('squier-mini-stratocaster-v-arendu',True).get_text(' ',strip=True)
        mikro=self.page('ibanez-pgmm31-v-arendu',True).get_text(' ',strip=True)
        pb=self.page('squier-mini-precision-bass-v-arendu',True).get_text(' ',strip=True)
        gsrm=self.page('ibanez-gsrm20-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('22,75',mini)
        self.assertIn('22,2',mikro)
        self.assertIn('28,6',pb)
        self.assertIn('28,6',gsrm)

    def test_quality_routes_are_brand_independent(self):
        guitar=self.page('elektrogitara-dlya-nebolshoy-ruki',True).get_text(' ',strip=True).casefold()
        bass=self.page('bas-gitara-korotkoy-menzury-dlya-nebolshoy-ruki',True).get_text(' ',strip=True).casefold()
        self.assertIn('мензур',guitar)
        self.assertIn('вес',guitar)
        self.assertIn('мензур',bass)
        self.assertIn('ширин',bass)

    def test_models_remain_distinct_not_ranked(self):
        alltext=' '.join(self.page(s,True).get_text(' ',strip=True) for s in SLUGS)
        self.assertIn('SSS',alltext)
        self.assertIn('хамбак',alltext.casefold())
        self.assertIn('P/J',alltext)
        self.assertNotIn('лучшая электрогитара',alltext.casefold())
        self.assertNotIn('лучший бас',alltext.casefold())

    def test_evidence_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],6)
        self.assertEqual(len(self.ledger['records']),6)
        self.assertEqual(self.ledger['sources']['mini_strat_beginner']['kind'],'manufacturer_education')
        for rec in self.ledger['records']:
            self.assertEqual(rec['availability'],'unconfirmed')
            for sid in rec['source_ids']:
                self.assertIn(sid,self.ledger['sources'])

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
          'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
