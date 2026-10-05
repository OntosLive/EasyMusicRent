"""Accordion size ladder and long-horizon upright learning standards."""
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
 'weltmeister-perle-v-arendu',
 'weltmeister-rubin-v-arendu',
 'yamaha-u1-v-arendu',
 'kawai-k300-v-arendu',
}

class AccordionUprightLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz66-accordion-upright-learning-standards.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/accordion-upright-learning-evidence.json',{})
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
        self.assertEqual(result['subjects'],1096)
        new={p['slug'] for p in self.doc['pages'] if p.get('mode')!='enrich'}
        self.assertEqual(new,SLUGS-{'yamaha-u1-v-arendu'})
        enrich=[p for p in self.doc['pages'] if p.get('mode')=='enrich']
        self.assertEqual([p['slug'] for p in enrich],['yamaha-u1-v-arendu'])
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_accordion_models_are_distinct_size_steps(self):
        perle=self.page('weltmeister-perle-v-arendu',True).get_text(' ',strip=True)
        rubin=self.page('weltmeister-rubin-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('26',perle)
        self.assertIn('48',perle)
        self.assertIn('30',rubin)
        self.assertIn('60',rubin)
        self.assertNotEqual(perle,rubin)

    def test_uprights_are_long_horizon_not_mandatory_beginner_models(self):
        text=' '.join(self.page(s,True).get_text(' ',strip=True) for s in ('yamaha-u1-v-arendu','kawai-k300-v-arendu'))
        self.assertTrue('годами' in text.casefold() or 'запасом роста' in text.casefold())
        self.assertNotIn('обязательный первый',text.casefold())
        self.assertNotIn('лучш',text.casefold())

    def test_evidence_is_bounded(self):
        self.assertEqual(self.ledger['new_subjects'],3)
        self.assertEqual(len(self.ledger['records']),4)
        self.assertEqual(self.ledger['sources']['latvia']['kind'],'education_equipment_official')
        self.assertEqual(self.ledger['sources']['kawai_de']['kind'],'manufacturer_education')
        for record in self.ledger['records']:
            self.assertEqual(record['availability'],'unconfirmed')

    def test_parent_navigation(self):
        acc={a['href'] for a in self.page('arenda-akkordeona-moskva',True).select('#razdely a[href]')}
        self.assertIn('/weltmeister-perle-v-arendu/',acc)
        self.assertIn('/weltmeister-rubin-v-arendu/',acc)
        piano={a['href'] for a in self.page('akusticheskoe-pianino',True).select('#razdely a[href]')}
        self.assertIn('/yamaha-u1-v-arendu/',piano)
        self.assertIn('/kawai-k300-v-arendu/',piano)

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
          'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
