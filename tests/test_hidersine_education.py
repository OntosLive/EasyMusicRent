"""Hidersine educational family keeps teacher-linked evidence bounded."""
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
 'smychkovye-hidersine',
 'hidersine-vivente-skripka-v-arendu',
 'hidersine-vivente-academy-skripka-v-arendu',
 'hidersine-vivente-alt-v-arendu',
 'hidersine-vivente-violonchel-v-arendu',
 'hidersine-vivente-kontrabas-v-arendu',
}

class HidersineEducationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz64-hidersine-education-family.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/hidersine-education-evidence.json',{})
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

    def test_brand_is_child_of_bowed_family(self):
        brand=self.page('smychkovye-hidersine',True)
        self.assertEqual(brand.select_one('.site-footer a')['href'],'/details/smychkovye/')
        root={a['href'] for a in self.page('',True).select('#razdely a[href]')}
        self.assertNotIn('/smychkovye-hidersine/',root)

    def test_teacher_linked_claim_is_bounded(self):
        text=' '.join(self.page(s,True).get_text(' ',strip=True) for s in SLUGS)
        self.assertIn('ESTA',text)
        self.assertNotIn('официальный стандарт европы',text.casefold())
        self.assertNotIn('обязательная модель',text.casefold())
        self.assertEqual(self.ledger['sources']['academy_violin']['kind'],'manufacturer_teacher_linked')

    def test_family_covers_four_bowed_voices(self):
        hrefs={a['href'] for a in self.page('smychkovye-hidersine',True).select('#razdely a[href]')}
        for href in (
          '/hidersine-vivente-skripka-v-arendu/',
          '/hidersine-vivente-alt-v-arendu/',
          '/hidersine-vivente-violonchel-v-arendu/',
          '/hidersine-vivente-kontrabas-v-arendu/',
        ):
            self.assertIn(href,hrefs)

    def test_evidence_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],6)
        self.assertEqual(len(self.ledger['records']),6)
        for record in self.ledger['records']:
            self.assertEqual(record['availability'],'unconfirmed')
            for sid in record['source_ids']:
                self.assertIn(sid,self.ledger['sources'])

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'52692fae95ac56ce5c93328a0a4c3f7eb933ade9c66a6fbec9e9245cde1a9a26',
          'assets/canon.css':'699834b7f5983c453e7d8f5703fb56ebb30cf461896805926b7b68993e6338af',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
