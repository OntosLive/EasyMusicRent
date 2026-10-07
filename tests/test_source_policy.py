"""Publication boundaries for documentation, independent from retained research."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from source_policy import POLICY_PATH, PUBLIC_CLASSES, public_sources, source_class


def source(url, title='Документация'):
    return {'url': url, 'title': title}


class SourcePolicyTests(unittest.TestCase):
    def test_manufacturer_and_museum_are_public(self):
        records = [source('https://www.yamaha.com/en/musical_instrument_guide/piano/'),
                   source('https://pubs.shure.com/view/guide/SM58/en-US.pdf'),
                   source('https://www.metmuseum.org/art/collection/search/504534')]
        self.assertEqual(public_sources(records), records)

    def test_private_research_and_unknown_remain_separate(self):
        cases = {
            'https://musprokat.ru/catalog/': 'rental_research',
            'https://www.pigini.nl/webwinkel/': 'retail_research',
            'https://ip-orchestra.ru/wp-content/uploads/2018/12/tehnicheskiy_rayder_ip_orchestra.pdf': 'context_research',
            'https://www.manualshelf.com/manual/moog.html': 'secondary_research',
            'https://unreviewed-brand.example/manual.pdf': 'unreviewed',
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(source_class(source(url)), expected)
                self.assertEqual(public_sources([source(url)]), [])

    def test_a_brand_name_in_title_does_not_authorize_an_unknown_host(self):
        self.assertEqual(public_sources([source('https://unreviewed.example/manual',
                                               'Official Yamaha manufacturer documentation')]), [])

    def test_exact_host_boundaries_and_unreviewed_subdomains(self):
        for host in ('www.yamaha.com.evil.example', 'notyamaha.com',
                     'forum.yamaha.com', 'yamaha.com.evil', 'www-yamaha.com'):
            with self.subTest(host=host):
                self.assertEqual(source_class(source('https://' + host + '/')), 'unreviewed')
        self.assertIn(source_class(source('https://WWW.YAMAHA.COM/guide')), PUBLIC_CLASSES)

    def test_only_http_https_without_credentials_or_ambiguous_characters(self):
        invalid_urls = (
            'javascript:alert(1)', 'data:text/html,hello', 'file:///manual.pdf',
            '//www.yamaha.com/manual', '/manual.pdf', 'https:///www.yamaha.com/manual',
            'https://www.yamaha.com@evil.example/manual',
            'https://attacker@www.yamaha.com/manual',
            'https://www.yamaha.com\\@evil.example/manual',
            'https://www.yamaha.com:invalid/manual', 'https://www.yamaha.com:8080/manual',
            'https://[broken/manual', ' https://www.yamaha.com/manual',
            'https://www.yamaha.com/line\nbreak', 'https://www.yamaha.com/white space',
            'https://www.yamaha.com./manual',
        )
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertEqual(source_class(source(url)), 'invalid')
        for url in ('http://www.yamaha.com/manual', 'https://www.yamaha.com:443/manual',
                    'http://www.yamaha.com:80/manual'):
            with self.subTest(url=url):
                self.assertIn(source_class(source(url)), PUBLIC_CLASSES)

    def test_shared_host_approval_is_for_exact_document(self):
        url = ('https://assets.ctfassets.net/javen7msabdh/5yGO5Slu3bppUANqqAImQR/'
               '1a5bfd3c073bc6394e67d713b3065c76/M3311.402_JCM800_2203_QSG_Web.pdf')
        self.assertIn(source_class(source(url)), PUBLIC_CLASSES)
        self.assertEqual(source_class(source(url.replace('M3311.402_', 'other_'))), 'unreviewed')
        self.assertEqual(source_class(source(url + '?redirect=other')), 'unreviewed')
        self.assertEqual(source_class(source('https://assets.ctfassets.net/unknown/manual.pdf')), 'unreviewed')

    def test_mixed_store_only_publishes_reviewed_own_model(self):
        own = 'https://goronok.ru/shop/skripka-goronok-nova-1-10/'
        other = 'https://goronok.ru/catalog/muzykalnye-instrumenty/'
        self.assertEqual(public_sources([source(own), source(other)]), [source(own)])
        self.assertEqual(source_class(source(own + '?other=1')), 'retail_research')

    def test_preserves_authored_order_without_arbitrary_cap(self):
        records = [source('https://www.yamaha.com/manual-' + str(n)) for n in range(5)]
        self.assertEqual(public_sources(records), records)

    def test_exact_url_duplicate_keeps_first_label_and_preserves_input(self):
        first = source('https://pubs.shure.com/view/guide/SM58/en-US.pdf', 'Первый заголовок')
        duplicate = source(first['url'], 'Повтор')
        records = [first, source('https://musprokat.ru/'), duplicate]
        before = deepcopy(records)
        selected = public_sources(records)
        self.assertEqual(selected, [first])
        self.assertEqual(records, before)
        selected[0]['title'] = 'Изменение результата'
        self.assertEqual(records, before)

    def test_different_fragment_is_not_silently_deduplicated(self):
        records = [source('https://www.yamaha.com/manual#one'),
                   source('https://www.yamaha.com/manual#two')]
        self.assertEqual(public_sources(records), records)

    def test_invalid_records_are_not_renderable(self):
        for record in (None, '', {}, {'url': 'https://www.yamaha.com/'},
                       {'url': None, 'title': 'Название'},
                       {'url': 1, 'title': 'Название'},
                       {'url': 'https://www.yamaha.com/', 'title': '  '}):
            with self.subTest(record=record):
                self.assertEqual(source_class(record), 'invalid')
                self.assertEqual(public_sources([record]), [])
        self.assertEqual(public_sources([]), [])

    def test_reviewed_config_has_no_conflicting_host_groups(self):
        policy = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
        hosts = [h for values in policy['host_groups'].values() for h in values]
        self.assertEqual(len(hosts), len(set(hosts)))
        self.assertTrue(set(policy['host_groups']) <= set(policy['classes']))
        self.assertTrue(set(policy['exact_url_rules'].values()) <= set(policy['classes']))
        for url, expected in policy['exact_url_rules'].items():
            with self.subTest(url=url):
                self.assertEqual(source_class(source(url)), expected)


if __name__ == '__main__':
    unittest.main()
