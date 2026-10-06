"""Student cornet learning routes and small-hand ergonomics."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

SLUGS={'yamaha-ycr2330iii-v-arendu','besson-prodige120-v-arendu','kornet-dlya-nebolshoy-ruki'}

class StudentCornetLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz77-student-cornet-learning.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/student-cornet-learning-evidence.json',{})
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

    def test_models_are_peers_not_ranked(self):
        y=self.page('yamaha-ycr2330iii-v-arendu',True).get_text(' ',strip=True)
        b=self.page('besson-prodige120-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('YCR‑2330III',y)
        self.assertIn('Prodige 120',b)
        alltext=y+' '+b
        self.assertNotIn('лучший корнет',alltext.casefold())
        self.assertNotIn('победитель',alltext.casefold())

    def test_small_hand_route_is_functional(self):
        q=self.page('kornet-dlya-nebolshoy-ruki',True).get_text(' ',strip=True).casefold()
        self.assertIn('третьего крона',q)
        self.assertIn('кист',q)
        self.assertIn('вес',q)

    def test_cornet_remains_child_of_existing_family(self):
        links={a['href'] for a in self.page('kornet',True).select('#razdely a[href]')}
        for slug in SLUGS:
            self.assertIn('/'+slug+'/',links)
        root={a['href'] for a in self.page('',True).select('#razdely a[href]')}
        self.assertNotIn('/yamaha-ycr2330iii-v-arendu/',root)

    def test_evidence_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],3)
        self.assertEqual(len(self.ledger['records']),3)
        for rec in self.ledger['records']:
            self.assertEqual(rec['availability'],'unconfirmed')

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
          'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
