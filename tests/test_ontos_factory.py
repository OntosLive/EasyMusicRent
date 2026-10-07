from pathlib import Path
import copy
import json
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from ontos_factory.engine import build_from_json, validate, build
from ontos_factory.portfolio import read_portfolio, prioritize, report, score
from ontos_factory.briefs import draft_assignment


class FactoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / 'tools/ontos_factory/sample_contrabass_repair.json'
        cls.config = json.loads(cls.path.read_text(encoding='utf-8'))
        cls.styles = ROOT / 'tools/ontos_factory/site.css'

    def test_one_hundred_distinct_hypotheses(self):
        rows = read_portfolio(ROOT / 'data/niche_factory/100_hypotheses.csv', expected_count=100)
        self.assertEqual(len({r['name'] for r in rows}), 100)
        self.assertTrue(all(r['status']=='гипотеза, не проверена' for r in rows))
        self.assertEqual(len(prioritize(rows)), 10)
        self.assertIn('гипотезы', report(rows).lower())
        self.assertTrue(all(20 <= score(r) <= 100 for r in rows))

    def test_brief_uses_specific_problem_and_does_not_claim_availability(self):
        niche=read_portfolio(ROOT/'data/niche_factory/100_hypotheses.csv')[0]
        text=draft_assignment(niche)
        self.assertIn(niche['name'],text)
        self.assertIn('исполнитель ещё не проверен',text)
        self.assertIn(niche['human_situation'],text)

    def test_draft_has_contact_noindex_no_sitemap_or_forms(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'preview'
            summary = build_from_json(self.path, output)
            self.assertEqual(summary['html_pages'], 4)
            self.assertEqual(summary['status'], 'draft')
            self.assertFalse((output/'sitemap.xml').exists())
            self.assertEqual((output/'robots.txt').read_text(encoding='utf-8'),'User-agent: *\nDisallow: /\n')
            for index in output.rglob('index.html'):
                text=index.read_text(encoding='utf-8')
                self.assertIn('noindex,nofollow',text)
                self.assertIn('tel:+79690532096',text)
                self.assertNotIn('<form',text)
                self.assertNotIn('rel="canonical"',text)
                self.assertNotIn('<script',text)

    def test_live_site_is_blocked_without_all_verifications(self):
        config=copy.deepcopy(self.config)
        config['status']='publish'
        with self.assertRaisesRegex(ValueError,'domain'):
            validate(config)
        config['domain']='https://real-test-site.ru'
        for key in ('executor_verified','contact_verified','offer_reviewed','legal_reviewed'):
            with self.assertRaisesRegex(ValueError,key):
                validate(config)
            config[key]=True
        config['operator_name']='Тестовый оператор'
        config['privacy_notice']='Условия обработки данных описываются оператором до публикации.'
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'published'
            result=build(config,output,self.styles)
            self.assertEqual(result['html_pages'],5)
            self.assertTrue(result['sitemap'])
            self.assertIn('https://real-test-site.ru/',(output/'sitemap.xml').read_text(encoding='utf-8'))
            self.assertNotIn('noindex',(output/'index.html').read_text(encoding='utf-8'))
            self.assertTrue((output/'privacy/index.html').exists())

    def test_different_scenarios_and_escaping(self):
        config=copy.deepcopy(self.config)
        config['pages'][1]['situation'] += '<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as tmp:
            result=build(config,Path(tmp)/'site',self.styles)
            html=(Path(tmp)/'site/podstavka-kontrabasa/index.html').read_text(encoding='utf-8')
            self.assertIn('&lt;script&gt;',html)
            self.assertNotIn('<script>',html)
            self.assertIn('Подставка контрабаса',html)
            self.assertNotIn('Трещина деки контрабаса',html)
            self.assertEqual(result['html_pages'],4)

    def test_duplicate_slugs_and_titles_disallowed(self):
        c=copy.deepcopy(self.config)
        c['pages'][1]['slug']=c['pages'][0]['slug']
        with self.assertRaisesRegex(ValueError,'repeated slug'):
            validate(c)
        c=copy.deepcopy(self.config)
        c['pages'][1]['title']=c['pages'][0]['title']
        with self.assertRaisesRegex(ValueError,'Repeated page title'):
            validate(c)

    def test_non_empty_directory_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'site'
            build(self.config,out,self.styles)
            with self.assertRaisesRegex(ValueError,'empty'):
                build(self.config,out,self.styles)


if __name__=='__main__':
    unittest.main()
