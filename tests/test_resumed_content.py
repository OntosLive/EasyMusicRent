"""Guard content-layer completion without changing the established page frame."""
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import site_core as core

LAYERS = ('92-electronic-subcategories.json', '93-historical-subcategories.json')


class ResumedContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temporary.name)
        cls.report = core.build(ROOT, cls.output)
        metadata = core.read_json(ROOT / 'content/legacy-metadata.json', {})
        cls.original = core.read_legacy(ROOT, metadata)
        cls.pages = core.read_legacy(ROOT, metadata)
        core.merge_records(ROOT, cls.pages)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def page(self, path):
        return core.soup((self.output / path.strip('/') / 'index.html').read_text(encoding='utf-8'))

    def test_editorial_titles_do_not_reuse_rental_request(self):
        # Nonidentical titles can still copy the commercial request.
        commercial = re.compile(r'\b(?:аренд\w*|прокат\w*|напрокат)\b', re.I)
        for record in self.report['pages']:
            with self.subTest(slug=record['slug']):
                if self.pages[record['slug']].kind == 'guide':
                    continue
                self.assertIsNone(commercial.search(record['editorial_title']))

    def test_new_subjects_have_complete_pairs_and_specific_blocks(self):
        for layer in LAYERS:
            document = core.read_json(ROOT / 'content/sections' / layer, {})
            for record in document['pages']:
                with self.subTest(slug=record['slug']):
                    entry = self.page('/' + record['slug'] + '/')
                    deep = self.page('/details/' + record['slug'] + '/')
                    self.assertEqual(core.text(entry.h1), record['search_title'])
                    self.assertEqual(core.text(deep.h1), record['editorial_title'])
                    self.assertEqual(len(deep.select('.arguments > article')), 3)
                    self.assertGreater(len(core.text(deep.select_one('main')).split()), 150)
                    self.assertTrue(deep.select_one('.wordmark'))
                    self.assertTrue(deep.select_one('.site-footer a[href]'))
                    self.assertTrue(record.get('sources'))

    def test_completed_parent_grids_have_no_inactive_cells(self):
        for slug in ('elektronnye', 'istoricheskie'):
            with self.subTest(slug=slug):
                deep = self.page('/details/' + slug + '/')
                self.assertIsNotNone(deep.select_one('#razdely'))
                self.assertEqual(deep.select('#razdely .pending'), [])

    def test_preexisting_routes_are_preserved_in_parent_grids(self):
        expected = {
            'elektronnye': {'sintezatory', 'midi-klaviatury', 'elektricheskaya-arfa'},
            'istoricheskie': {'istoricheskie-klavishnye', 'klavesin', 'klavikord',
                              'istoricheskoe-fortepiano', 'istoricheskaya-arfa', 'lyutnya', 'teorba'},
        }
        for parent, children in expected.items():
            actual = {core.url_slug(a['href']) for a in self.page('/details/' + parent + '/').select('#razdely a[href]')}
            self.assertTrue(children <= actual, (parent, children - actual))

    def test_model_heading_repairs_preserve_original_good_copy(self):
        document = core.read_json(ROOT / 'content/sections/94-model-editorial-titles.json', {})
        self.assertEqual(len(document['pages']), 39)
        for record in document['pages']:
            slug = record['slug']
            with self.subTest(slug=slug):
                self.assertEqual(self.pages[slug].intro, self.original[slug].intro)
                self.assertEqual(self.pages[slug].blocks, self.original[slug].blocks)
                self.assertEqual(self.pages[slug].search_title, self.original[slug].search_title)
                self.assertEqual(self.pages[slug].editorial_title, record['editorial_title'])


if __name__ == '__main__':
    unittest.main()
