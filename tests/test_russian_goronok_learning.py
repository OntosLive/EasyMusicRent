"""Russian Goronok educational ladder stays distinct by tier and size."""
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import site_core as core
import content_inventory as inventory

SLUGS={
 'smychkovye-goronok',
 'goronok-nova-v-arendu',
 'goronok-etyud-v-arendu',
 'goronok-kapris-v-arendu',
 'goronok-kadentsiya-v-arendu',
 'goronok-fantaziya-v-arendu',
 'goronok-aleksey-romanov-v-arendu',
 'goronok-nova-alt-v-arendu',
 'goronok-kadentsiya-alt-v-arendu',
 'goronok-nova-violonchel-v-arendu',
 'goronok-kadentsiya-violonchel-v-arendu',
 'goronok-nova-kontrabas-v-arendu',
 'goronok-kadentsiya-kontrabas-v-arendu',
 'goronok-aleksey-romanov-kontrabas-v-arendu',
}

class RussianGoronokTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=[
            core.read_json(ROOT/'content/sections/zz62-russian-goronok-learning-ladder.json',{}),
            core.read_json(ROOT/'content/sections/zz63-goronok-bowed-family-expansion.json',{}),
        ]
        cls.pages=[p for d in cls.docs for p in d['pages']]
        cls.ledger=core.read_json(ROOT/'docs/research/russian-goronok-learning-evidence.json',{})
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
        self.assertEqual(result['subjects'],1110)
        self.assertEqual({p['slug'] for p in self.pages},SLUGS)
        for slug in SLUGS:
            self.assertTrue(self.page(slug).find('h1'))
            self.assertTrue(self.page(slug,True).find('h1'))

    def test_brand_is_bowed_child_not_root_family(self):
        page=self.page('smychkovye-goronok',True)
        self.assertEqual(page.select_one('.site-footer a')['href'],'/details/smychkovye/')
        links={a['href'] for a in page.select('#razdely a[href]')}
        for slug in SLUGS-{'smychkovye-goronok'}:
            self.assertIn('/'+slug+'/',links)
        root={a['href'] for a in self.page('',True).select('#razdely a[href]')}
        self.assertNotIn('/smychkovye-goronok/',root)

    def test_education_tiers_are_explicit_and_not_flattened(self):
        text={p['slug']:str(p).casefold() for p in self.pages}
        for slug in ('goronok-nova-v-arendu','goronok-etyud-v-arendu','goronok-kapris-v-arendu'):
            self.assertIn('ученичес',text[slug])
        for slug in ('goronok-kadentsiya-v-arendu','goronok-fantaziya-v-arendu'):
            self.assertIn('студенчес',text[slug])
        self.assertIn('мастеров',text['goronok-aleksey-romanov-v-arendu'])
        self.assertIn('1/8',text['goronok-aleksey-romanov-v-arendu'])
        self.assertIn('4/4',text['goronok-aleksey-romanov-v-arendu'])

    def test_evidence_scope_and_availability(self):
        self.assertEqual(self.ledger['new_subjects'],14)
        self.assertEqual(len(self.ledger['records']),14)
        self.assertEqual(self.ledger['sources']['classification']['kind'],'manufacturer_education')
        for r in self.ledger['records']:
            self.assertEqual(r['availability'],'unconfirmed')
        combined=' '.join(self.page(s,True).get_text(' ',strip=True) for s in SLUGS)
        self.assertNotIn('государственный стандарт',combined.casefold())
        self.assertNotIn('лучшая скрипка россии',combined.casefold())

    def test_compiler_and_css_unchanged(self):
        expected={
          'scripts/site_core.py':'63020f3adbf21715a6e67848135ae0bcc20effcb389886f60ab48f502ad3ca8d',
          'assets/canon.css':'0b048bad40e448f643e67e5a5bd20e16872d1f8953f9e926e009aba2bd6e0b54',
        }
        for path,digest in expected.items():
            self.assertEqual(sha256((ROOT/path).read_bytes()).hexdigest(),digest)

if __name__=='__main__':
    unittest.main()
