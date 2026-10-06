"""Free-bass accordion education is a distinct left-hand-system route."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

SLUGS={'hohner-bravo-i-49f-v-arendu','akkordeon-s-vybornym-basom-dlya-obucheniya'}

class FreeBassAccordionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz69-freebass-accordion-learning.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/freebass-accordion-learning-evidence.json',{})
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
        self.assertEqual(result['subjects'],1212)
        self.assertEqual({p['slug'] for p in self.doc['pages']},SLUGS)
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_freebass_is_system_not_prestige(self):
        text=self.page('akkordeon-s-vybornym-basom-dlya-obucheniya',True).get_text(' ',strip=True)
        self.assertIn('систем',text.casefold())
        self.assertIn('левой',text.casefold())
        self.assertNotIn('престиж',text.casefold())

    def test_bravo49f_keeps_teacher_linked_evidence_bounded(self):
        text=self.page('hohner-bravo-i-49f-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('преподавател',text.casefold())
        self.assertNotIn('обязательн',text.casefold())
        self.assertEqual(self.ledger['sources']['bravo49f']['kind'],'manufacturer_teacher_linked')

    def test_evidence_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],2)
        self.assertEqual(len(self.ledger['records']),2)
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
