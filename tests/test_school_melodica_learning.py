"""School melodica learning category and 32-key standards."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

SLUGS={'melodika','yamaha-p32d-v-arendu','suzuki-m32c-v-arendu','melodika-32-klavishi-dlya-shkoly'}

class SchoolMelodicaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz76-school-melodica-learning.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/school-melodica-learning-evidence.json',{})
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
        self.assertEqual(next(p for p in self.doc['pages'] if p['slug']=='melodika').get('mode'),'enrich')
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_category_keeps_existing_keyboard_parent(self):
        cat=self.page('melodika',True)
        self.assertEqual(cat.select_one('.site-footer a')['href'],'/details/klavishnye/')
        root={a['href'] for a in self.page('',True).select('#razdely a[href]')}
        self.assertNotIn('/melodika/',root)

    def test_two_school_models_and_quality_route_stay_distinct(self):
        y=self.page('yamaha-p32d-v-arendu',True).get_text(' ',strip=True)
        s=self.page('suzuki-m32c-v-arendu',True).get_text(' ',strip=True)
        q=self.page('melodika-32-klavishi-dlya-shkoly',True).get_text(' ',strip=True)
        self.assertIn('32',y)
        self.assertIn('32',s)
        self.assertIn('32',q)
        self.assertIn('P‑32D',y)
        self.assertIn('M‑32C',s)
        self.assertNotIn('лучшая мелодика',q.casefold())

    def test_school_guidance_is_not_universalized(self):
        text=' '.join(self.page(s,True).get_text(' ',strip=True) for s in SLUGS)
        self.assertNotIn('обязательный стандарт',text.casefold())
        self.assertNotIn('единственная правильная',text.casefold())
        self.assertEqual(self.ledger['sources']['suzuki_faq']['kind'],'manufacturer_education_guidance')

    def test_evidence_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],3)
        self.assertEqual(len(self.ledger['records']),4)
        self.assertEqual(next(r for r in self.ledger['records'] if r['slug']=='melodika')['action'],'enrich')
        for rec in self.ledger['records']:
            self.assertEqual(rec['availability'],'unconfirmed')

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'01a4af94326065d30cfddfaf7974c7763ba3a9f81911add3ca84052caea36256',
          'assets/canon.css':'04fd0f6c6ff73b23eb9676765fe3d94d7921e9b83800d920615146799ea8e12f',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
