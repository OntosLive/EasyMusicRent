"""Digital-piano learning core links mature model pages from one school comparison scene."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

MODEL_SLUGS={'roland-fp30x-v-arendu','kawai-es120-v-arendu','casio-pxs1100-v-arendu'}
SCHOOL='cifrovoe-pianino-dlya-muzykalnoy-shkoly'

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

    def test_inventory_stays_1090_and_only_school_scene_is_enriched(self):
        result=inventory.inspect(ROOT)
        self.assertEqual(result['errors'],[])
        self.assertEqual(result['subjects'],1111)
        self.assertEqual(len(self.doc['pages']),1)
        p=self.doc['pages'][0]
        self.assertEqual(p['slug'],SCHOOL)
        self.assertEqual(p.get('mode'),'enrich')
        self.assertTrue(p['append_intro'])
        self.assertFalse({'search_title','editorial_title','parent','intro','blocks'} & p.keys())

    def test_mature_model_routes_and_original_titles_survive(self):
        expected={
          'roland-fp30x-v-arendu':'Roland FP-30X: ежедневная практика в переносном формате',
          'kawai-es120-v-arendu':'Kawai ES120: начать занятия и сохранить мобильность',
          'casio-pxs1100-v-arendu':'Casio PX-S1100: ежедневные занятия и возможность переезда',
        }
        for slug,title in expected.items():
            self.assertTrue(self.page(slug).find('h1'))
            self.assertEqual(core.text(self.page(slug,True).h1),title)

    def test_school_scene_links_all_peer_models(self):
        links={a['href'] for a in self.page(SCHOOL,True).select('#razdely a[href]')}
        for slug in MODEL_SLUGS:
            self.assertIn('/'+slug+'/',links)
        text=self.page(SCHOOL,True).get_text(' ',strip=True)
        for name in ('P‑225','FP‑30X','ES120','PX‑S1100'):
            self.assertIn(name,text)
        self.assertNotIn('лучшее цифровое пианино',text.casefold())
        self.assertNotIn('победитель',text.casefold())

    def test_evidence_is_comparison_context_not_model_rewrite(self):
        self.assertEqual(self.ledger['new_subjects'],0)
        self.assertEqual(self.ledger['enriched_subjects'],[SCHOOL])
        self.assertEqual(len(self.ledger['records']),1)
        self.assertEqual(self.ledger['records'][0]['action'],'enrich')
        self.assertEqual(self.ledger['sources']['pianino_ru']['kind'],'specialist_editorial_commercial')

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
          'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
