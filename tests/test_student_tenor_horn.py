"""Student tenor-horn learning routes and Eb brass-band distinction."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

SLUGS={'tenor-gorn','yamaha-yah203-v-arendu','besson-prodige152-v-arendu'}

class StudentTenorHornTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz79-student-tenor-horn-learning.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/student-tenor-horn-learning-evidence.json',{})
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

    def test_tenor_horn_is_eb_and_distinct(self):
        text=self.page('tenor-gorn',True).get_text(' ',strip=True).casefold()
        self.assertIn('eb',text)
        self.assertIn('brass band',text)
        self.assertIn('эуфониум',text)
        self.assertIn('валторн',text)
        self.assertNotIn('это тот же инструмент',text)

    def test_student_models_are_peers_not_ranked(self):
        y=self.page('yamaha-yah203-v-arendu',True).get_text(' ',strip=True)
        b=self.page('besson-prodige152-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('YAH‑203',y)
        self.assertIn('Prodige 152',b)
        alltext=(y+' '+b).casefold()
        self.assertNotIn('лучший тенор-горн',alltext)
        self.assertNotIn('победитель',alltext)

    def test_category_lives_under_brass_family(self):
        page=self.page('tenor-gorn',True)
        self.assertEqual(page.select_one('.site-footer a')['href'],'/details/mednye-duhovye/')
        links={a['href'] for a in page.select('#razdely a[href]')}
        self.assertIn('/yamaha-yah203-v-arendu/',links)
        self.assertIn('/besson-prodige152-v-arendu/',links)
        root={a['href'] for a in self.page('',True).select('#razdely a[href]')}
        self.assertNotIn('/tenor-gorn/',root)

    def test_evidence_and_availability(self):
        self.assertEqual(self.ledger['baseline_subjects'],1135)
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
