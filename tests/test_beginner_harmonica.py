"""Beginner harmonica learning routes and bounded evidence."""
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
 'gubnaya-garmonika',
 'hohner-special20-c-v-arendu',
 'gubnaya-garmonika-v-do-mazhore-dlya-obucheniya',
 'gubnaya-garmonika-s-legkim-otklikom',
}

class BeginnerHarmonicaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz75-beginner-harmonica-learning.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/beginner-harmonica-learning-evidence.json',{})
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
        self.assertEqual(result['subjects'],1148)
        self.assertEqual({p['slug'] for p in self.doc['pages']},SLUGS)
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_category_is_child_of_traditional_family(self):
        category=self.page('gubnaya-garmonika',True)
        self.assertEqual(category.select_one('.site-footer a')['href'],'/details/traditsionnye/')
        root={a['href'] for a in self.page('',True).select('#razdely a[href]')}
        self.assertNotIn('/gubnaya-garmonika/',root)

    def test_special20_and_c_are_not_universalized(self):
        text=' '.join(self.page(s,True).get_text(' ',strip=True) for s in SLUGS)
        self.assertIn('Special 20',text)
        self.assertIn('C',text)
        self.assertNotIn('обязательная гармоника',text.casefold())
        self.assertNotIn('единственно правильная',text.casefold())
        self.assertNotIn('официальный стандарт',text.casefold())

    def test_quality_route_is_brand_independent(self):
        text=self.page('gubnaya-garmonika-s-legkim-otklikom',True).get_text(' ',strip=True).casefold()
        self.assertIn('гермет',text)
        self.assertIn('отклик',text)
        self.assertIn('бренд',text)

    def test_evidence_scope_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],4)
        self.assertEqual(len(self.ledger['records']),4)
        self.assertEqual(self.ledger['sources']['tomlin_special']['kind'],'teacher_recommendation')
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
