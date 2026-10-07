"""School percussion kits, student mallet models and Russian exam scene."""
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
 'uchebnye-komplekty-udarnyh',
 'pearl-sk910-v-arendu',
 'pearl-pk910-v-arendu',
 'pearl-pl910c-v-arendu',
 'yamaha-yx2035pr-v-arendu',
 'yamaha-yx135-v-arendu',
 'adams-academy-xylophone-v-arendu',
 'adams-academy-marimba-v-arendu',
 'ksilofon-s-reguliruemoy-vysotoy',
 'udarnye-dlya-ekzamena-ksilofon-i-malyy-baraban',
}

class SchoolPercussionCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz80-school-percussion-core.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/school-percussion-core-evidence.json',{})
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

    def test_learning_kits_are_distinct(self):
        sk=self.page('pearl-sk910-v-arendu',True).get_text(' ',strip=True)
        pk=self.page('pearl-pk910-v-arendu',True).get_text(' ',strip=True)
        pl=self.page('pearl-pl910c-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('14×5,5',sk)
        self.assertIn('2,5',pk)
        self.assertIn('малый барабан',pl.casefold())
        self.assertIn('bells',pl)
        joined=(sk+' '+pk+' '+pl).casefold()
        self.assertNotIn('единственный правильный комплект',joined)

    def test_legacy_and_current_yamaha_are_not_collapsed(self):
        legacy=self.page('yamaha-yx135-v-arendu',True).get_text(' ',strip=True).casefold()
        current=self.page('yamaha-yx2035pr-v-arendu',True).get_text(' ',strip=True).casefold()
        self.assertIn('снят',legacy)
        self.assertIn('преемник',current)
        self.assertIn('регулиров',current)
        self.assertIn('фиксирован',legacy)

    def test_height_is_brand_independent_quality_route(self):
        q=self.page('ksilofon-s-reguliruemoy-vysotoy',True).get_text(' ',strip=True)
        self.assertIn('Yamaha',q)
        self.assertIn('Adams',q)
        self.assertIn('плеч',q.casefold())
        self.assertNotIn('лучший ксилофон',q.casefold())

    def test_russian_exam_scene_keeps_two_instrument_functions(self):
        q=self.page('udarnye-dlya-ekzamena-ksilofon-i-malyy-baraban',True).get_text(' ',strip=True).casefold()
        self.assertIn('ксилофон',q)
        self.assertIn('малый барабан',q)
        self.assertIn('экзам',q)
        self.assertIn('пэд',q)

    def test_category_remains_child_of_percussion(self):
        cat=self.page('uchebnye-komplekty-udarnyh',True)
        self.assertEqual(cat.select_one('.site-footer a')['href'],'/details/udarnye/')
        links={a['href'] for a in cat.select('#razdely a[href]')}
        for href in ('/pearl-sk910-v-arendu/','/pearl-pk910-v-arendu/','/pearl-pl910c-v-arendu/'):
            self.assertIn(href,links)
        root={a['href'] for a in self.page('',True).select('#razdely a[href]')}
        self.assertNotIn('/uchebnye-komplekty-udarnyh/',root)

    def test_evidence_scope_and_availability(self):
        self.assertEqual(self.ledger['baseline_subjects'],1138)
        self.assertEqual(self.ledger['new_subjects'],10)
        self.assertEqual(len(self.ledger['records']),10)
        self.assertEqual(self.ledger['sources']['russian_exam']['kind'],'school_curriculum_official')
        self.assertEqual(self.ledger['sources']['yamaha_yx135_eu']['kind'],'manufacturer_status')
        for rec in self.ledger['records']:
            self.assertEqual(rec['availability'],'unconfirmed')

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'52692fae95ac56ce5c93328a0a4c3f7eb933ade9c66a6fbec9e9245cde1a9a26',
          'assets/canon.css':'04fd0f6c6ff73b23eb9676765fe3d94d7921e9b83800d920615146799ea8e12f',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
