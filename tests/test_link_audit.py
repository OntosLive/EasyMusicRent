"""Graph hygiene and metric semantics on small authored/legacy fixtures."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import link_audit
import site_core as core


class LinkAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "content/sections").mkdir(parents=True)
        self.write_legacy("")

    def write_legacy(self, slug, navigation=""):
        path = self.root / slug / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '<title>Аренда музыкальных инструментов</title><main><h1>Инструменты</h1>'
            f'<div class="cluster-family-grid">{navigation}</div></main>',
            encoding="utf-8",
        )

    def write_json(self, path, value):
        (self.root / path).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def section(self, name, **document):
        self.write_json(f"content/sections/{name}.json", document)

    def record(self, slug, parent="", links=None):
        return {
            "slug": slug,
            "search_title": f"{slug} в аренду",
            "editorial_title": slug,
            "description": "Описание",
            "kicker": "Инструмент",
            "intro": ["<p>Содержательный ввод.</p>"],
            "blocks": [{"title": "Выбор", "paragraphs": ["Что проверить."]}],
            "parent": parent,
            "links": links or [],
        }

    def link(self, target, label="Маршрут"):
        return {"href": f"/{target}/", "label": label}

    def compiled_route_count(self):
        pages = core.read_legacy(self.root, {})
        core.merge_records(self.root, pages)
        core.merge_legacy_navigation(self.root, pages)
        aliases = core.read_json(self.root / "content/aliases.json", {})
        for slug in aliases:
            pages.pop(slug, None)
        core.connect(pages, aliases)
        return sum(bool(item.get("href")) for page in pages.values() for item in page.links)

    def test_aliases_entry_details_and_old_base_are_one_subject_route(self):
        first_href = "/EasyMusicRent/details/old-beta/index.html#choice"
        self.section("00-pages", pages=[
            self.record("alpha", links=[
                {"href": first_href, "label": "Первый"},
                self.link("beta", "Канонический"),
                {"href": "/details/beta/?view=full", "label": "Раскрытие"},
                {"label": "Подпись без ссылки"},
                self.link("gamma", "Одинаковая подпись"),
                self.link("delta", "Одинаковая подпись"),
            ]),
            self.record("beta"), self.record("gamma"), self.record("delta"),
        ])
        self.write_json("content/aliases.json", {"old-beta": "beta"})

        report = link_audit.audit(self.root)

        self.assertEqual(report["duplicate_route_count"], 2)
        self.assertEqual(report["self_link_count"], 0)
        self.assertEqual(report["error_count"], 2)
        self.assertEqual(report["link_edges"], 3)
        self.assertEqual(report["link_edges"], self.compiled_route_count())
        self.assertEqual(report["pages_with_links"], 1)
        self.assertEqual(report["lateral_coverage_pct"], 20.0)
        duplicate = report["details"]["duplicate_routes"][0]
        self.assertEqual(duplicate["canonical_target"], "beta")
        self.assertEqual(duplicate["source_slug"], "alpha")
        self.assertEqual(duplicate["link_index"], 1)
        self.assertEqual(duplicate["first_link"]["href"], first_href)
        self.assertEqual(duplicate["matching_definitions"],
                         ["content/sections/00-pages.json#/pages/0/links/1"])

    def test_self_links_do_not_create_outgoing_inbound_or_model_coverage(self):
        self.section("00-pages", pages=[
            self.record("family"),
            self.record("alpha-v-arendu", parent="family", links=[
                self.link("old-alpha"),
                {"href": "/details/alpha-v-arendu/", "label": "Снова к себе"},
            ]),
        ])
        self.write_json("content/aliases.json", {"old-alpha": "alpha-v-arendu"})

        report = link_audit.audit(self.root)

        self.assertEqual(report["self_link_count"], 2)
        self.assertEqual(report["duplicate_route_count"], 1)
        self.assertEqual(report["error_count"], 3)
        for graph in (report, report["strict_lateral"]):
            self.assertEqual(graph["link_edges"], 0)
            self.assertEqual(graph["pages_with_links"], 0)
            self.assertEqual(graph["pages_without_lateral_inbound"], 3)
            self.assertEqual(graph["model_lateral_coverage_pct"], 0.0)
            self.assertEqual(graph["model_thin_leaves"], 1)
        self.assertEqual(report["details"]["thin_leaf_slugs"], ["", "alpha-v-arendu"])

    def test_hierarchy_is_explicit_navigation_but_not_strict_lateral(self):
        self.section("00-pages", pages=[
            self.record("family", links=[self.link("alpha-v-arendu"), self.link("peer-v-arendu")]),
            self.record("alpha-v-arendu", parent="family", links=[
                self.link("family"), self.link("accessory"), self.link("peer-v-arendu"),
            ]),
            self.record("peer-v-arendu", parent="family", links=[self.link("family")]),
            self.record("accessory", parent="alpha-v-arendu", links=[self.link("alpha-v-arendu")]),
            self.record("unlinked-child", parent="family"),
        ])

        report = link_audit.audit(self.root)

        self.assertEqual(report["errors"], [])
        self.assertEqual(report["link_edges"], 7)
        self.assertEqual(self.compiled_route_count(), 8)  # Automatic child route stays outside this audit.
        self.assertEqual(report["pages_with_links"], 4)
        self.assertEqual(report["thin_leaf_pages"], 2)
        self.assertEqual(report["model_lateral_coverage_pct"], 100.0)
        strict = report["strict_lateral"]
        self.assertEqual(strict["link_edges"], 1)  # alpha -> peer is the only sibling route.
        self.assertEqual(strict["pages_with_links"], 1)
        self.assertEqual(strict["lateral_coverage_pct"], 16.67)
        self.assertEqual(strict["thin_leaf_pages"], 4)
        self.assertEqual(strict["pages_without_lateral_inbound"], 5)
        self.assertEqual(strict["model_lateral_coverage_pct"], 50.0)
        self.assertEqual(strict["model_thin_leaves"], 1)
        self.assertEqual(report["details"]["strict_lateral"]["model_thin_leaf_slugs"], ["peer-v-arendu"])

    def test_replaced_links_ignored_enrich_links_and_retired_alias_page_do_not_fail(self):
        self.section("00-pages", pages=[
            self.record("alpha", links=[self.link("alpha"), self.link("alpha"), self.link("missing")]),
            self.record("beta"),
            self.record("old-alpha", links=[self.link("missing")]),
        ])
        self.section("10-replace", navigation_replace={"alpha": [self.link("beta")]})
        self.section("20-enrich", pages=[{
            "slug": "alpha", "mode": "enrich", "intro": ["<p>Обновлённое введение.</p>"],
            "links": [self.link("alpha"), self.link("missing")],
        }])
        self.write_json("content/aliases.json", {"old-alpha": "alpha"})

        report = link_audit.audit(self.root)

        self.assertEqual(report["errors"], [])
        self.assertEqual(report["subjects"], 3)
        self.assertEqual(report["link_edges"], 1)
        self.assertEqual(report["duplicate_route_count"], 0)
        self.assertEqual(report["self_link_count"], 0)

    def test_diagnostics_locate_cross_file_navigation_duplicate(self):
        self.section("00-pages", pages=[
            self.record("alpha", links=[self.link("beta", "Исходный")]), self.record("beta"),
        ])
        self.section("10-bridge", navigation={"alpha": [self.link("beta", "Добавленный")]})

        report = link_audit.audit(self.root)

        duplicate = report["details"]["duplicate_routes"][0]
        self.assertEqual(duplicate["page_source"], "content/sections/00-pages.json")
        self.assertEqual(duplicate["matching_definitions"],
                         ["content/sections/10-bridge.json#/navigation/alpha/0"])
        self.assertEqual(duplicate["first_link"]["matching_definitions"],
                         ["content/sections/00-pages.json#/pages/0/links/0"])
        self.assertIn("10-bridge.json", report["errors"][0])

    def test_legacy_map_duplicate_reports_preserved_html_source(self):
        self.write_legacy("alpha", '<a href="/beta/">Исходный</a><span>Подпись</span>')
        path = self.root / "alpha/karta/index.html"
        path.parent.mkdir()
        path.write_text('<div class="fund-scenes"><a href="/details/beta/">'
                        '<span class="fund-scene-title">Сохранённый</span></a></div>', encoding="utf-8")
        self.section("00-pages", pages=[self.record("beta")])

        report = link_audit.audit(self.root)

        self.assertEqual(report["duplicate_route_count"], 1)
        duplicate = report["details"]["duplicate_routes"][0]
        self.assertEqual(duplicate["matching_definitions"],
                         ["alpha/karta/index.html:.fund-scenes a[href] item 1"])
        self.assertEqual(duplicate["first_link"]["page_source"], "alpha/index.html")

    def test_missing_alias_parent_and_link_targets_still_block(self):
        self.section("00-pages", pages=[self.record("alpha", parent="missing-parent", links=[self.link("missing")])])
        self.write_json("content/aliases.json", {"old-alpha": "missing-alias-target"})

        report = link_audit.audit(self.root)

        self.assertEqual(report["error_count"], 3)
        self.assertIn("alpha: missing parent missing-parent", report["errors"])
        self.assertIn("alpha: missing linked subject /missing/", report["errors"])
        self.assertIn("alias old-alpha: missing target missing-alias-target", report["errors"])

    def test_cli_fails_for_each_hygiene_fault_and_saves_diagnostics(self):
        report_path = self.root / "_audit/link-report.json"
        cases = (
            ([self.link("beta"), self.link("beta")], "duplicate_route_count"),
            ([self.link("alpha")], "self_link_count"),
        )
        for links, counter in cases:
            with self.subTest(counter=counter):
                self.section("00-pages", pages=[self.record("alpha", links=links), self.record("beta")])
                with mock.patch.object(sys, "argv", ["link_audit.py", "--root", str(self.root), "--report", str(report_path)]):
                    with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                        link_audit.main()
                self.assertEqual(result.exception.code, 1)
                saved = json.loads(report_path.read_text(encoding="utf-8"))
                self.assertEqual(saved[counter], 1)
                self.assertEqual(saved["error_count"], 1)
                self.assertTrue(saved["details"]["duplicate_routes"] or saved["details"]["self_links"])

        self.section("00-pages", pages=[self.record("alpha", links=[self.link("beta")]), self.record("beta")])
        with mock.patch.object(sys, "argv", ["link_audit.py", "--root", str(self.root)]):
            with contextlib.redirect_stdout(io.StringIO()):
                link_audit.main()  # A clean graph succeeds without an override or baseline allowance.


if __name__ == "__main__":
    unittest.main()
