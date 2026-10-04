"""Source registry regressions: rendered URLs do not require source folders."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import content_inventory as registry


class ContentInventoryTests(unittest.TestCase):
    def test_complete_registry_has_no_collisions(self):
        result=registry.inspect(ROOT)
        self.assertEqual(result['errors'], [])
        self.assertGreaterEqual(result['subjects'], 741)

    def test_generated_synth_exists_without_a_source_directory(self):
        result=registry.inspect(ROOT)
        entry=next(p for p in result['pages'] if p['slug']=='sintezator-dlya-studii')
        self.assertIn('100c-',entry['source'])
        self.assertFalse((ROOT/'sintezator-dlya-studii/index.html').exists())

    def test_all_eight_old_synth_topics_have_one_owner(self):
        items=registry.inspect(ROOT)['pages']
        for record in json.loads((ROOT/'content/sections/100c-synth-scenario-landings.json').read_text())['pages']:
            self.assertEqual(sum(p['slug']==record['slug'] for p in items),1)
        self.assertFalse((ROOT/'content/sections/zz13-synth-final-landings.json').exists())

    def test_candidate_duplicate_is_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'candidate.json'
            path.write_text(json.dumps({'pages':[{'slug':'sintezator-dlya-studii','search_title':'Other name'}]}))
            result=registry.inspect(ROOT,[path])
            self.assertTrue(any('duplicate declarations' in e and 'sintezator-dlya-studii' in e for e in result['errors']))

    def test_candidate_duplicate_request_is_rejected(self):
        current=registry.inspect(ROOT)['pages'][0]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'candidate.json'
            path.write_text(json.dumps({'pages':[{'slug':'inventory-collision-fixture','search_title':current['search_title']}]}))
            result=registry.inspect(ROOT,[path])
            self.assertTrue(any('duplicate request' in e for e in result['errors']))

if __name__=='__main__':
    unittest.main()
