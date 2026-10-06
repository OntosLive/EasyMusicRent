"""Student baritone-horn learning routes and score distinction."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

SLUGS={'bariton-gorn','yamaha-ybh301-v-arendu','besson-prodige157-v-arendu','bariton-ili-evfonium-po-partii'}

class StudentBaritoneHornTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz78-student-baritone-horn-learning.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/student-baritone-horn-evidence.json',{})
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

    def test_baritone_is_distinct_from_euphonium(self):
        text=self.page('bariton-gorn',True).get_text(' ',strip=True).casefold()
        self.assertIn('эуфониум',text)
        self.assertIn('узк',text)
        self.assertIn('ярк',text)
        q=self.page('bariton-ili-evfonium-po-partii',True).get_text(' ',strip=True).casefold()
        self.assertIn('парт',q)
        self.assertIn('замен',q)

    def test_student_models_are_peers_not_ranked(self):
        y=self.page('yamaha-ybh301-v-arendu',True).get_text(' ',strip=True)
        b=self.page('besson-prodige157-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('YBH‑301',y)
        self.assertIn('Prodige 157',b)
        alltext=(y+' '+b).casefold()
        self.assertNotIn('лучший баритон',alltext)
        self.assertNotIn('победитель',alltext)

    def test_category_is_bowed_into_existing_brass_tree(self):
        page=self.page('bariton-gorn',True)
        self.assertEqual(page.select_one('.site-footer a')['href'],'/details/mednye-duhovye/')
        links={a['href'] for a in page.select('#razdely a[href]')}
        for slug in SLUGS-{'bariton-gorn'}:
            self.assertIn('/'+slug+'/',links)

    def test_evidence_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],4)
        self.assertEqual(len(self.ledger['records']),4)
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
