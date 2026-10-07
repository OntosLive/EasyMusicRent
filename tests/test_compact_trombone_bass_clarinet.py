"""Regression coverage for compact trombone and student bass-clarinet learning routes."""
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
 'yamaha-ysl350c-v-arendu',
 'trombon-dlya-korotkoy-ruki',
 'yamaha-ycl221ii-v-arendu',
 'jupiter-jbc1000-v-arendu',
 'bas-klarinet-dlya-obucheniya',
}

class CompactTromboneBassClarinetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz73-compact-trombone-student-bass-clarinet.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/compact-trombone-bass-clarinet-evidence.json',{})
        cls.temp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.temp.name)
        core.build(ROOT,cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self,slug,deep=False):
        return core.soup((self.output/('details' if deep else '')/slug/'index.html').read_text())

    def test_inventory_and_one_owner(self):
        result=inventory.inspect(ROOT)
        self.assertEqual(result['errors'],[])
        self.assertGreaterEqual(result['subjects'],1212)
        self.assertEqual({p['slug'] for p in self.doc['pages']},NEW)
        for slug in NEW:
            self.assertEqual(sum(x['slug']==slug for x in result['pages']),1,slug)

    def test_compact_trombone_preserves_standard_logic(self):
        text=self.page('yamaha-ysl350c-v-arendu',True).get_text(' ',strip=True).casefold()
        self.assertIn('стандарт',text)
        self.assertIn('повышающий вентиль',text)
        quality=self.page('trombon-dlya-korotkoy-ruki',True).get_text(' ',strip=True).casefold()
        self.assertIn('длин',quality)
        self.assertIn('плеч',quality)

    def test_student_bass_clarinet_routes_are_distinct(self):
        y=self.page('yamaha-ycl221ii-v-arendu',True).get_text(' ',strip=True)
        j=self.page('jupiter-jbc1000-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('двухчаст',y.casefold())
        self.assertTrue('case' in y.casefold() or 'кейс' in y.casefold() or 'футляр' in y.casefold())
        self.assertIn('высота шпиля',j.casefold())
        self.assertIn('школьн',j.casefold())
        quality=self.page('bas-klarinet-dlya-obucheniya',True).get_text(' ',strip=True).casefold()
        self.assertIn('транспорт',quality)
        self.assertIn('посад',quality)

    def test_navigation_from_existing_parents(self):
        trom={a['href'] for a in self.page('trombon',True).select('#razdely a[href]')}
        self.assertIn('/yamaha-ysl350c-v-arendu/',trom)
        self.assertIn('/trombon-dlya-korotkoy-ruki/',trom)
        bass={a['href'] for a in self.page('bas-klarinet',True).select('#razdely a[href]')}
        for href in (
          '/yamaha-ycl221ii-v-arendu/',
          '/jupiter-jbc1000-v-arendu/',
          '/bas-klarinet-dlya-obucheniya/',
        ):
            self.assertIn(href,bass)

    def test_evidence_scope_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],5)
        self.assertEqual(len(self.ledger['records']),5)
        for rec in self.ledger['records']:
            self.assertEqual(rec['availability'],'unconfirmed')
            for sid in rec['source_ids']:
                self.assertIn(sid,self.ledger['sources'])

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'52692fae95ac56ce5c93328a0a4c3f7eb933ade9c66a6fbec9e9245cde1a9a26',
          'assets/canon.css':'04fd0f6c6ff73b23eb9676765fe3d94d7921e9b83800d920615146799ea8e12f',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
