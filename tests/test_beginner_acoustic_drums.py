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
        self.assertEqual(result['subjects'],1125)
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
          'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
          'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
