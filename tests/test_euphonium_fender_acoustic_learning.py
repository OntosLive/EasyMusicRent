"""Regression coverage for lightweight euphonium and Fender acoustic learning routes."""
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
 'legkiy-evfonium-rebenku',
 'fender-cd60s-v-arendu',
 'fender-cc60s-v-arendu',
}
ENRICH='akusticheskaya-gitara-po-razmeru-uchenika'

class EuphoniumFenderAcousticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz72-euphonium-fender-acoustic-learning.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/euphonium-fender-acoustic-learning-evidence.json',{})
        cls.temp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.temp.name)
        core.build(ROOT,cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self,slug,deep=False):
        return core.soup((self.output/('details' if deep else '')/slug/'index.html').read_text())

    def test_inventory_and_subject_ownership(self):
        result=inventory.inspect(ROOT)
        self.assertEqual(result['errors'],[])
        self.assertGreaterEqual(result['subjects'],1212)
        created={p['slug'] for p in self.doc['pages'] if p.get('mode')!='enrich'}
        self.assertEqual(created,NEW)
        for slug in NEW:
            self.assertEqual(sum(x['slug']==slug for x in result['pages']),1,slug)

    def test_acoustic_size_page_is_enriched_only(self):
        p=next(x for x in self.doc['pages'] if x['slug']==ENRICH)
        self.assertEqual(p.get('mode'),'enrich')
        self.assertTrue(p['append_intro'])
        self.assertFalse({'search_title','editorial_title','parent','intro','blocks'} & p.keys())

    def test_body_shapes_are_not_ranked(self):
        cd=self.page('fender-cd60s-v-arendu',True).get_text(' ',strip=True)
        cc=self.page('fender-cc60s-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('dreadnought',cd.casefold())
        self.assertIn('concert',cc.casefold())
        combined=(cd+' '+cc).casefold()
        self.assertNotIn('лучше для всех',combined)
        self.assertNotIn('обязательный выбор',combined)

    def test_euphonium_quality_route_is_live(self):
        text=self.page('legkiy-evfonium-rebenku',True).get_text(' ',strip=True).casefold()
        self.assertIn('мас',text)
        self.assertIn('3+1',text)
        links={a['href'] for a in self.page('evfonium',True).select('#razdely a[href]')}
        self.assertIn('/yamaha-yep201-v-arendu/',links)
        self.assertIn('/legkiy-evfonium-rebenku/',links)

    def test_evidence_scope_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],3)
        self.assertEqual(set(self.ledger['enriched_subjects']),{ENRICH,'yamaha-yep201-v-arendu'})
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
