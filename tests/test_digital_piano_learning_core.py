"""Multi-brand digital-piano learning core remains non-ranked and source-bounded."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

SLUGS={'roland-fp30x-v-arendu','kawai-es120-v-arendu','casio-pxs1100-v-arendu'}

class DigitalPianoLearningCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=core.read_json(ROOT/'content/sections/zz65-digital-piano-learning-core.json',{})
        cls.ledger=core.read_json(ROOT/'docs/research/digital-piano-learning-core-evidence.json',{})
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
        self.assertEqual(result['subjects'],1093)
        new={p['slug'] for p in self.doc['pages'] if p.get('mode')!='enrich'}
        self.assertEqual(new,SLUGS)
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_school_page_is_enriched_not_replaced(self):
        enrich=[p for p in self.doc['pages'] if p.get('mode')=='enrich']
        self.assertEqual([p['slug'] for p in enrich],['cifrovoe-pianino-dlya-muzykalnoy-shkoly'])
        p=enrich[0]
        self.assertTrue(p['append_intro'])
        self.assertFalse({'search_title','editorial_title','parent','intro','blocks'} & p.keys())

    def test_peer_models_are_not_ranked(self):
        text=' '.join(self.page(s,True).get_text(' ',strip=True) for s in SLUGS)
        self.assertNotIn('лучшее цифровое пианино',text.casefold())
        self.assertNotIn('победитель',text.casefold())
        for name in ('FP‑30X','ES120','PX‑S1100'):
            self.assertIn(name,text)

    def test_learning_functions_are_distinct(self):
        fp=self.page('roland-fp30x-v-arendu',True).get_text(' ',strip=True)
        es=self.page('kawai-es120-v-arendu',True).get_text(' ',strip=True)
        px=self.page('casio-pxs1100-v-arendu',True).get_text(' ',strip=True)
        self.assertIn('PHA‑4',fp)
        self.assertIn('Responsive Hammer Compact',es)
        self.assertIn('Duet',px)

    def test_evidence_is_bounded(self):
        self.assertEqual(self.ledger['new_subjects'],3)
        self.assertEqual(len(self.ledger['records']),4)
        self.assertEqual(self.ledger['sources']['pianino_ru']['kind'],'specialist_editorial_commercial')
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
