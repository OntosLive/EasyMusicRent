"""Lightweight registry checks for the first large guitar human-scene wave."""
from pathlib import Path
import json
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import content_inventory as inventory

FILES=[
 'content/sections/zz81-acoustic-guitar-human-scenes.json',
 'content/sections/zz82-electric-guitar-human-scenes.json',
 'content/sections/zz83-bass-guitar-human-scenes.json',
 'content/sections/zz84-special-classical-guitar-human-scenes.json',
]
EXPECTED_COUNTS=[20,20,16,8]

class GuitarHumanSceneWaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=[json.loads((ROOT/p).read_text(encoding='utf-8')) for p in FILES]
        cls.pages=[p for d in cls.docs for p in d['pages']]
        cls.registry=inventory.inspect(ROOT)
        cls.by_slug={p['slug']:p for p in cls.registry['pages']}

    def test_wave_size_and_inventory(self):
        self.assertEqual([len(d['pages']) for d in self.docs],EXPECTED_COUNTS)
        self.assertEqual(len(self.pages),64)
        self.assertEqual(len({p['slug'] for p in self.pages}),64)
        self.assertEqual(self.registry['errors'],[])
        self.assertEqual(self.registry['subjects'],1212)

    def test_each_scene_has_one_owner_and_complete_shape(self):
        all_records=self.registry['pages']
        for p in self.pages:
            slug=p['slug']
            self.assertEqual(sum(x['slug']==slug for x in all_records),1,slug)
            self.assertTrue(p.get('parent'),slug)
            self.assertTrue(p.get('search_title'),slug)
            self.assertTrue(p.get('editorial_title'),slug)
            self.assertTrue(p.get('description'),slug)
            self.assertEqual(len(p.get('blocks',[])),3,slug)
            self.assertTrue(p.get('quote'),slug)

    def test_internal_links_point_to_registered_subjects(self):
        for p in self.pages:
            for link in p.get('links',[]):
                href=link.get('href','')
                if not (href.startswith('/') and href.endswith('/')):
                    continue
                slug=href.strip('/').split('/')[-1]
                if slug in {'details','usloviya'}:
                    continue
                self.assertIn(slug,self.by_slug,(p['slug'],href))

if __name__=='__main__':
    unittest.main()
