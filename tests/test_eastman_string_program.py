"""Samuel Eastman string-program family keeps existing VL100 and adds missing bowed voices."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

NEW={
 'smychkovye-eastman',
 'eastman-vc100-v-arendu',
}
EXISTING={'eastman-vl100-v-arendu','eastman-va100-v-arendu','eastman-vb80-v-arendu'}

class EastmanStringProgramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz71-eastman-string-program-family.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/eastman-string-program-evidence.json',{})
        cls.temp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.temp.name)
        core.build(ROOT,cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self,slug,deep=False):
        return core.soup((self.output/('details' if deep else '')/slug/'index.html').read_text())

    def test_inventory_and_new_subjects(self):
        result=inventory.inspect(ROOT)
        self.assertEqual(result['errors'],[])
        self.assertEqual(result['subjects'],1125)
        self.assertEqual({p['slug'] for p in self.doc['pages']},NEW)
        for slug in NEW|EXISTING:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_existing_vl100_is_linked_not_redeclared(self):
        self.assertFalse(any(p['slug'] in EXISTING for p in self.doc['pages']))
        links={a['href'] for a in self.page('smychkovye-eastman',True).select('#razdely a[href]')}
        for slug in EXISTING:
            self.assertIn('/'+slug+'/',links)

    def test_four_bowed_voices_are_connected(self):
        links={a['href'] for a in self.page('smychkovye-eastman',True).select('#razdely a[href]')}
        for href in (
          '/eastman-vl100-v-arendu/',
          '/eastman-va100-v-arendu/',
          '/eastman-vc100-v-arendu/',
          '/eastman-vb80-v-arendu/',
        ):
            self.assertIn(href,links)

    def test_school_rental_claim_is_bounded(self):
        vb=self.page('eastman-vb80-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('школ',vb.casefold())
        self.assertIn('аренд',vb.casefold())
        self.assertIn('Rubner',vb)
        self.assertNotIn('обязательный стандарт',vb.casefold())
        self.assertEqual(self.ledger['sources']['vb80']['kind'],'manufacturer_school_rental')

    def test_evidence_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],2)
        self.assertEqual(set(self.ledger['existing_subjects']),EXISTING)
        self.assertEqual(len(self.ledger['records']),5)
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
