"""Beginner acoustic drum size routes stay distinct and ergonomic."""
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
 'yamaha-rydeen-v-arendu',
 'tama-imperialstar-v-arendu',
 'barabannaya-ustanovka-ponizhe-dlya-rebenka',
}

class BeginnerAcousticDrumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz67-beginner-acoustic-drum-sizes.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/beginner-acoustic-drum-size-evidence.json',{})
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
        self.assertGreaterEqual(result['subjects'],1212)
        self.assertEqual({p['slug'] for p in self.doc['pages']},SLUGS)
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_models_keep_distinct_size_logic(self):
        rydeen=self.page('yamaha-rydeen-v-arendu',True).get_text(' ',strip=True)
        tama=self.page('tama-imperialstar-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('20',rydeen)
        self.assertIn('22',rydeen)
        self.assertIn('18',tama)
        self.assertIn('22',tama)

    def test_quality_route_is_ergonomic_not_age_only(self):
        text=self.page('barabannaya-ustanovka-ponizhe-dlya-rebenka',True).get_text(' ',strip=True)
        self.assertIn('стул',text.casefold())
        self.assertIn('педал',text.casefold())
        self.assertNotIn('по возрасту',text.casefold())

    def test_evidence_bounded(self):
        self.assertEqual(self.ledger['new_subjects'],3)
        self.assertEqual(len(self.ledger['records']),3)
        for record in self.ledger['records']:
            self.assertEqual(record['availability'],'unconfirmed')

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'01a4af94326065d30cfddfaf7974c7763ba3a9f81911add3ca84052caea36256',
          'assets/canon.css':'04fd0f6c6ff73b23eb9676765fe3d94d7921e9b83800d920615146799ea8e12f',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
