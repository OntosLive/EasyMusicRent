"""Publication regressions for two independent, indexable documents per subject."""
from contextlib import contextmanager
from copy import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import site_core as core
from validate_site import validate


NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'
PAIR_ROUTES = ('/', '/details/', '/pianino/', '/details/pianino/')
CONDITIONS = (
    'ot-pervogo-zanyatiya-do-solnoy-stseny',
    'ot-odnogo-instrumenta-do-komplektatsii-orkestra',
    'srok-arendy',
    'stsena-zapis-semki',
    'bez-zaloga',
    'dostavka-po-moskve',
    'dostavka-po-rossii',
    'samovyvoz',
)


class IndexingContractTests(unittest.TestCase):
    """A real small build keeps failure cases independent of the large corpus."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.fixture = Path(cls.temporary.name)
        source = cls.fixture / 'source'
        source.mkdir()
        (source / 'assets').mkdir()
        (source / 'assets/canon.css').write_text('body { color: #111; }', encoding='utf-8')
        icons = ''.join(f'<a href="{href}"><svg viewBox="0 0 48 48"><path d="M0 0"/></svg></a>' for href in (core.TG, core.WA))
        for slug, query, heading in (
            ('', 'Аренда музыкальных инструментов в Москве', 'Музыкальные инструменты'),
            ('pianino', 'Прокат пианино в Москве', 'Пианино'),
        ):
            folder = source / slug
            folder.mkdir(exist_ok=True)
            nav = '<nav class="home-family-grid"><a href="/pianino/">Пианино</a></nav>' if not slug else ''
            (folder / 'index.html').write_text(
                f'<html><head><title>{query}</title><meta name="search-title" content="{query}"></head>'
                f'<body><main><h1>{heading}</h1><p class="deck">Выбор инструмента для занятий.</p>{nav}</main>{icons}</body></html>',
                encoding='utf-8',
            )
        for slug in (*CONDITIONS, 'masshtab', 'dostavka'):
            folder = source / 'usloviya' / slug
            folder.mkdir(parents=True)
            (folder / 'index.html').write_text(
                '<html><body><main><h1>Условия проката</h1><p class="deck">Согласуем детали по телефону.</p></main></body></html>',
                encoding='utf-8',
            )
        legacy = source / 'pianino/karta'
        legacy.mkdir()
        (legacy / 'index.html').write_text('<html><body></body></html>', encoding='utf-8')
        content = source / 'content'
        content.mkdir()
        (content / 'aliases.json').write_text('{"old-piano":"pianino"}', encoding='utf-8')
        sections = content / 'sections'
        sections.mkdir()
        (sections / '00-documentation.json').write_text(json.dumps({'pages': [{
            'slug': 'pianino', 'mode': 'enrich', 'sources': [{
                'title': 'Yamaha YUS — спецификация',
                'url': 'https://usa.yamaha.com/products/musical_instruments/pianos/upright_pianos/yus_series/specs.html',
            }],
        }]}, ensure_ascii=False), encoding='utf-8')
        cls.baseline = cls.fixture / 'built'
        cls.report = core.build(source, cls.baseline)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / 'site'
        shutil.copytree(self.baseline, self.output)

    def page(self, route):
        return core.soup((self.output / route.strip('/') / 'index.html').read_text(encoding='utf-8'))

    def assert_failure(self, fragment):
        errors = validate(self.output, self.report)['errors']
        self.assertTrue(any(fragment in error for error in errors), errors)

    @contextmanager
    def changed_page(self, route, change):
        path = self.output / route.strip('/') / 'index.html'
        original = path.read_bytes()
        doc = core.soup(original.decode('utf-8'))
        change(doc)
        path.write_text(str(doc), encoding='utf-8')
        try:
            yield
        finally:
            path.write_bytes(original)

    @contextmanager
    def changed_sitemap(self, change):
        path = self.output / 'sitemap.xml'
        original = path.read_bytes()
        tree = ET.parse(path)
        change(tree.getroot())
        tree.write(path, encoding='utf-8', xml_declaration=True)
        try:
            yield
        finally:
            path.write_bytes(original)

    @staticmethod
    def add_location(sitemap, url):
        node = ET.SubElement(sitemap, f'{{{NS}}}url')
        ET.SubElement(node, f'{{{NS}}}loc').text = url

    def test_both_documents_include_the_home_pair_in_sitemap(self):
        result = validate(self.output, self.report)
        self.assertEqual(result['errors'], [])
        self.assertEqual(self.report['source_pages'], 2)
        self.assertEqual(result['sitemap_entries'], 4)
        locations = [node.text for node in ET.parse(self.output / 'sitemap.xml').findall(f'{{{NS}}}url/{{{NS}}}loc')]
        self.assertEqual(set(locations), {core.DOMAIN + route for route in PAIR_ROUTES})
        for route in PAIR_ROUTES:
            with self.subTest(route=route):
                doc = self.page(route)
                self.assertNotIn('noindex', core.meta(doc, 'robots').casefold())
                self.assertEqual(doc.find('link', rel='canonical')['href'], core.DOMAIN + route)

    def test_conditions_and_redirects_keep_their_distinct_policy(self):
        self.assertEqual(self.report['conditions'], 8)
        locations = {node.text for node in ET.parse(self.output / 'sitemap.xml').findall(f'{{{NS}}}url/{{{NS}}}loc')}
        for slug in CONDITIONS:
            route = '/usloviya/' + slug + '/'
            self.assertNotIn('noindex', core.meta(self.page(route), 'robots'))
            self.assertNotIn(core.DOMAIN + route, locations)
        for route in ('/pianino/karta/', '/details/pianino/karta/', '/old-piano/', '/details/old-piano/', '/fond/', '/details/fond/', '/usloviya/masshtab/', '/usloviya/dostavka/'):
            doc = self.page(route)
            self.assertIsNotNone(doc.find('meta', attrs={'http-equiv': 'refresh'}))
            self.assertIn('noindex', core.meta(doc, 'robots'))
            self.assertNotIn(core.DOMAIN + route, locations)

    def test_documentation_is_collapsed_after_contact_and_footer(self):
        doc = self.page('/details/pianino/')
        source = doc.select_one('details.sources')
        self.assertIsNotNone(source)
        self.assertFalse(source.has_attr('open'))
        self.assertEqual(core.text(source.find('summary')), 'Документация')
        children = doc.select_one('.page').find_all(recursive=False)
        self.assertIs(children[-1], source)
        self.assertIs(children[-2], doc.select_one('.site-footer'))
        self.assertIsNotNone(doc.main.select_one('.contact'))
        self.assertIsNone(self.page('/pianino/').select_one('.sources'))
        self.assertIsNone(self.page('/details/').select_one('.sources'))

    def test_documentation_cannot_return_to_the_main_attention_flow(self):
        for change, message in (
            (lambda doc: doc.select_one('.sources summary').__setattr__('string', 'Об инструменте: источники'), 'documentation label is not canonical'),
            (lambda doc: doc.select_one('.sources').__setitem__('open', ''), 'documentation must be collapsed details'),
            (lambda doc: doc.select_one('.contact-block').insert_before(doc.select_one('.sources').extract()), 'documentation must follow contact and footer at page bottom'),
            (lambda doc: doc.select_one('.page').append(copy(doc.select_one('.sources'))), 'duplicate documentation blocks'),
        ):
            with self.subTest(message=message):
                with self.changed_page('/details/pianino/', change):
                    self.assert_failure(message)
    def test_noindex_on_either_document_is_rejected(self):
        for route in PAIR_ROUTES:
            with self.subTest(route=route):
                with self.changed_page(route, lambda doc: doc.head.append(doc.new_tag('meta', attrs={'name': 'robots', 'content': 'noindex,follow'}))):
                    self.assert_failure(route + ': indexable page accidentally noindex')
                    self.assert_failure('sitemap includes noindex: ' + core.DOMAIN + route)

    def test_engine_specific_and_none_directives_cannot_hide_noindex(self):
        for name, directive in (('Googlebot', 'NOINDEX, FOLLOW'), ('bingbot', 'none'), ('yandex', 'noindex'), ('ROBOTS', 'NONE')):
            with self.subTest(name=name, directive=directive):
                with self.changed_page('/details/pianino/', lambda doc: doc.head.append(doc.new_tag('meta', attrs={'name': name, 'content': directive}))):
                    self.assert_failure('/details/pianino/: indexable page accidentally noindex')

    def test_cross_canonical_is_rejected_in_both_directions(self):
        for route, target in (('/pianino/', '/details/pianino/'), ('/details/pianino/', '/pianino/')):
            with self.subTest(route=route):
                with self.changed_page(route, lambda doc: doc.find('link', rel='canonical').__setitem__('href', core.DOMAIN + target)):
                    self.assert_failure(route + ': invalid self-canonical')

    def test_same_path_on_foreign_domain_is_not_self_canonical(self):
        for route in ('/pianino/', '/details/pianino/'):
            with self.subTest(route=route):
                with self.changed_page(route, lambda doc: doc.find('link', rel='canonical').__setitem__('href', 'https://example.com' + route)):
                    self.assert_failure(route + ': invalid self-canonical')

    def test_missing_or_duplicate_canonical_is_rejected(self):
        for mutation in (
            lambda doc: doc.find('link', rel='canonical').decompose(),
            lambda doc: doc.head.append(copy(doc.find('link', rel='canonical'))),
        ):
            with self.changed_page('/details/pianino/', mutation):
                self.assert_failure('/details/pianino/: invalid self-canonical')

    def test_missing_sitemap_entry_is_rejected_for_both_layers_and_root(self):
        for route in PAIR_ROUTES:
            with self.subTest(route=route):
                def remove(sitemap):
                    for node in list(sitemap):
                        if node.find(f'{{{NS}}}loc').text == core.DOMAIN + route:
                            sitemap.remove(node)
                with self.changed_sitemap(remove):
                    self.assert_failure('sitemap absent pair URL: ' + core.DOMAIN + route)

    def test_sitemap_duplicate_is_not_hidden_by_set_comparison(self):
        with self.changed_sitemap(lambda sitemap: self.add_location(sitemap, core.DOMAIN + '/pianino/')):
            self.assert_failure('sitemap duplicate URL: ' + core.DOMAIN + '/pianino/')

    def test_conditions_redirects_and_other_urls_are_rejected_in_sitemap(self):
        for route in ('/usloviya/srok-arendy/', '/old-piano/', '/details/old-piano/', '/unpublished/', '/pianino/?view=all', '/details/pianino/#selection'):
            with self.subTest(route=route):
                with self.changed_sitemap(lambda sitemap: self.add_location(sitemap, core.DOMAIN + route)):
                    self.assert_failure('sitemap unexpected URL: ' + core.DOMAIN + route)
                    if route in ('/old-piano/', '/details/old-piano/'):
                        self.assert_failure('sitemap includes redirect: ' + core.DOMAIN + route)

    def test_foreign_or_non_https_sitemap_urls_are_rejected(self):
        for url in ('https://example.com/pianino/', core.DOMAIN.replace('https:', 'http:') + '/details/pianino/'):
            with self.subTest(url=url):
                with self.changed_sitemap(lambda sitemap: self.add_location(sitemap, url)):
                    self.assert_failure('sitemap foreign or non-HTTPS URL: ' + url)

    def test_malformed_sitemap_reports_failure_instead_of_crashing(self):
        (self.output / 'sitemap.xml').write_text('<urlset>', encoding='utf-8')
        self.assert_failure('sitemap unreadable:')

    def test_robots_cannot_block_the_editorial_documents(self):
        for agent in ('*', 'Googlebot', 'YandexBot', 'bingbot'):
            with self.subTest(agent=agent):
                (self.output / 'robots.txt').write_text(
                    f'User-agent: {agent}\nDisallow: /details/\nSitemap: {core.DOMAIN}/sitemap.xml\n',
                    encoding='utf-8',
                )
                self.assert_failure('robots.txt blocks ' + agent + ' pair pages:')
        (self.output / 'robots.txt').write_text(
            f'User-agent: *\nAllow: /\nDisallow: /details/\nSitemap: {core.DOMAIN}/sitemap.xml\n',
            encoding='utf-8',
        )
        self.assert_failure('robots.txt changes open crawl policy:')

    def test_robots_preserves_the_canonical_sitemap_declaration(self):
        (self.output / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n', encoding='utf-8')
        self.assert_failure('robots.txt missing canonical sitemap declaration')


if __name__ == '__main__':
    unittest.main()
