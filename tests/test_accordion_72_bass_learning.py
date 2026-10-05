"""72-bass accordion step-up routes stay functional and non-ranked."""
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
 'hohner-bravo-iii-72-v-arendu',
 'weltmeister-achat-34-72-v-arendu',
 'akkordeon-72-basa-dlya-prodolzheniya-obucheniya',
}

class Accordion72BassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz68-accordion-72-bass-learning-step.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/accordion-72-bass-learning-evidence.json',{})
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
        self.assertEqual(result['subjects'],1105)
        self.assertEqual({p['slug'] for p in self.doc['pages']},SLUGS)
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_step_up_is_range_vs_weight_not_prestige(self):
        text=self.page('akkordeon-72-basa-dlya-prodolzheniya-obucheniya',True).get_text(' ',strip=True)
        self.assertIn('72',text)
        self.assertIn('вес',text.casefold())
        self.assertIn('программ',text.casefold())
        self.assertNotIn('престиж',text.casefold())

    def test_models_keep_distinct_geometry(self):
        bravo=self.page('hohner-bravo-iii-72-v-arendu',True).get_text(' ',strip=True)
        achat=self.page('weltmeister-achat-34-72-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('7,4',bravo)
        self.assertIn('34',achat)
        self.assertNotEqual(bravo,achat)

    def test_evidence_bounded(self):
        self.assertEqual(self.ledger['new_subjects'],3)
        self.assertEqual(len(self.ledger['records']),3)
        self.assertEqual(self.ledger['sources']['bravo72']['kind'],'manufacturer_education')
        self.assertEqual(self.ledger['sources']['achat_bw']['kind'],'specialist_retail_category')
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
