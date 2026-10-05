"""Russian institutional evidence enriches existing student-wind pages without new routes."""
import json
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

BATCH='zz60-russian-school-wind-evidence.json'
TARGETS={
 'yamaha-yfl212-v-arendu',
 'yamaha-ycl255-v-arendu',
 'yamaha-yas280-v-arendu',
 'yamaha-yts280-v-arendu',
 'yamaha-ytr2330-v-arendu',
 'yamaha-ysl354-v-arendu',
}

class RussianSchoolWindEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections'/BATCH,{})
        cls.ledger=core.read_json(ROOT/'docs/research/russian-school-wind-evidence.json',{})
        cls.temp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.temp.name)
        cls.report=core.build(ROOT,cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self,slug,deep=False):
        return core.soup((self.output/('details' if deep else '')/slug/'index.html').read_text())

    def test_batch_is_enrichment_only_and_inventory_count_stays_1067(self):
        result=inventory.inspect(ROOT)
        self.assertEqual(result['errors'],[])
        self.assertEqual(result['subjects'],1139)
        self.assertEqual({p['slug'] for p in self.doc['pages']},TARGETS)
        self.assertTrue(all(p.get('mode')=='enrich' for p in self.doc['pages']))
        for p in self.doc['pages']:
            self.assertFalse({'search_title','editorial_title','parent','intro','blocks'} & p.keys())
            self.assertTrue(p['append_intro'])

    def test_all_existing_routes_survive(self):
        for slug in TARGETS:
            self.assertTrue(self.page(slug).find('h1'),slug)
            deep=self.page(slug,True)
            self.assertTrue(deep.find('h1'),slug)
            self.assertEqual(len(deep.select('.contact-block')),1)

    def test_russian_context_is_in_deep_copy_without_universal_recommendation(self):
        text=' '.join(self.page(slug,True).get_text(' ',strip=True) for slug in TARGETS)
        for marker in ('российск','Казани','Братск','Краснодар'):
            self.assertIn(marker.casefold(),text.casefold())
        self.assertNotIn('рекомендуют все российские',text.casefold())
        self.assertNotIn('обязательный стандарт россии',text.casefold())

    def test_evidence_types_keep_use_separate_from_recommendation(self):
        self.assertEqual(self.ledger['new_subjects'],0)
        self.assertEqual(set(self.ledger['enriched_subjects']),TARGETS)
        self.assertEqual(len(self.ledger['records']),6)
        kinds={s['kind'] for s in self.ledger['sources'].values()}
        self.assertIn('school_inventory_official',kinds)
        self.assertIn('municipal_inventory_official',kinds)
        self.assertIn('procurement_aggregator',kinds)
        self.assertIn('education_competition_report',kinds)
        for src in self.ledger['sources'].values():
            self.assertEqual(urlsplit(src['url']).scheme,'https')
            self.assertTrue(src['scope'])
        for record in self.ledger['records']:
            self.assertEqual(record['action'],'enrich')
            self.assertEqual(record['availability'],'unconfirmed')
            for sid in record['source_ids']:
                self.assertIn(sid,self.ledger['sources'])

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
          'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
