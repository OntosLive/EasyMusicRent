"""Exact model-authored search titles must not be Python-composed copy."""
from html import escape
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import apply_authored_titles as authored


class AuthoredTitlesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.site = self.root / "site"
        self.site.mkdir()
        self.manifest = self.root / "titles.json"
        self.titles = {
            "": {
                "n0": "Аренда музыкальных инструментов | Можно обсудить разные сроки аренды",
                "n1": "Музыкальные инструменты | Устройство определяет способ извлечения звука",
            },
            "skripka": {
                "n0": "Скрипка ребёнку в аренду | Да, можно организовать аренду на нужный срок",
                "n1": "Скрипка для занятий | Положение руки определяет доступность позиций",
            },
        }
        self._write_manifest(self.titles)
        for route in ("", "details", "skripka", "details/skripka", "other"):
            path = self.site / route / "index.html"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                '<!doctype html><html lang="ru"><head><title>Исходное название</title>'
                '<meta name="description" content="Описание"></head>'
                '<body><main><h1>Текст не меняется</h1></main></body></html>',
                encoding="utf-8",
            )

    def _write_manifest(self, pairs):
        self.manifest.write_text(
            json.dumps({"schema_version": 1, "pairs": pairs}, ensure_ascii=False),
            encoding="utf-8",
        )

    def test_entire_model_written_title_is_published_without_changing_h1(self):
        report = authored.apply(self.site, self.manifest)
        self.assertEqual((report["model_authored_titles"], report["modified"]), (4, 4))
        self.assertFalse(report["automatic_text_generation"])
        for slug, pair in self.titles.items():
            for role in ("n0", "n1"):
                path = self.site / ("details/" + slug if role == "n1" else slug) / "index.html"
                html = path.read_text(encoding="utf-8")
                self.assertIn(f"<title>{escape(pair[role])}</title>", html)
                self.assertIn("<h1>Текст не меняется</h1>", html)
                self.assertIn('name="description" content="Описание"', html)
        self.assertIn("<title>Исходное название</title>",
                      (self.site / "other/index.html").read_text(encoding="utf-8"))

    def test_repeated_publication_does_not_modify_anything(self):
        authored.apply(self.site, self.manifest)
        self.assertEqual(authored.apply(self.site, self.manifest)["modified"], 0)
        self.assertEqual(authored.apply(self.site, self.manifest, check=True)["modified"], 0)

    def test_missing_or_unedited_title_fails_the_publication_check(self):
        authored.apply(self.site, self.manifest)
        (self.site / "skripka/index.html").write_text(
            '<html><head><title>Прежняя версия</title></head></html>', encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "Authored title not installed"):
            authored.apply(self.site, self.manifest, check=True)

    def test_missing_topic_stops_without_partial_writes(self):
        self.titles["missing-slug"] = self.titles["skripka"].copy()
        # Unique strings so the missing-path preflight is exercised.
        self.titles["missing-slug"]["n0"] += " для проверки"
        self.titles["missing-slug"]["n1"] += " для проверки"
        self._write_manifest(self.titles)
        with self.assertRaisesRegex(ValueError, "does not exist"):
            authored.apply(self.site, self.manifest)
        self.assertIn("<title>Исходное название</title>",
                      (self.site / "index.html").read_text(encoding="utf-8"))

    def test_automatic_brand_or_duplicate_titles_are_rejected(self):
        self.titles["skripka"]["n0"] += " | ONTOS.RENT"
        self._write_manifest(self.titles)
        with self.assertRaises(ValueError):
            authored.validate_manifest(self.manifest)
        self.titles["skripka"]["n0"] = self.titles[""]["n0"]
        self._write_manifest(self.titles)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            authored.validate_manifest(self.manifest)

    def test_no_authoring_on_technical_aliases(self):
        pairs = authored.validate_manifest(authored.DEFAULT_MANIFEST)
        aliases = json.loads((ROOT / "content" / "aliases.json").read_text(encoding="utf-8"))
        self.assertFalse(set(pairs) & set(aliases))

    def test_current_gpt6_corpus_is_canonical_and_source_reviewed(self):
        pairs = authored.validate_manifest(authored.DEFAULT_MANIFEST)
        manifest = json.loads(authored.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["publication_status"], "model_reviewed_pilot")
        self.assertTrue(manifest["requires_owner_review"])
        self.assertEqual(len(pairs), 853)
        self.assertEqual(len({t for v in pairs.values() for t in v.values()}), 1706)
        self.assertIn("Полный размер для концерта", pairs["kontrabas-chetyre-chetverti-v-arendu"]["n0"])
        self.assertIn("период подготовки", pairs["skripka-na-konkurs-v-arendu"]["n0"])
        self.assertNotIn("Сверьте мензуру", pairs["kontrabas-chetyre-chetverti-v-arendu"]["n0"])
        self.assertIn("полного состава", pairs["instrumenty-dlya-studencheskogo-kamernogo-orkestra"]["n0"])
        self.assertIn("Рояль", pairs["instrumenty-dlya-fortepiannogo-kvinteta"]["n0"])
        self.assertIn("тихой практики", pairs["instrument-esli-slishkom-gromko-dlya-doma"]["n1"])

    def test_only_gpt6_family_authors_public_title_copy(self):
        manifest = json.loads(authored.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["authoring_models"], ["GPT-6", "GPT-6.1"])
        self.assertEqual(manifest["python_role"], "literal_transfer_validation_coverage_only")
        self.assertEqual(len(manifest["pairs"]), 853)

    def test_title_can_be_direct_without_vertical_separator(self):
        self.titles["skripka"]["n0"] = "Скрипка ребёнку в аренду на нужный срок"
        self._write_manifest(self.titles)
        pairs = authored.validate_manifest(self.manifest)
        self.assertEqual(pairs["skripka"]["n0"], "Скрипка ребёнку в аренду на нужный срок")
        self.assertEqual(authored.apply(self.site, self.manifest)["modified"], 4)

    def test_empty_manifest_requires_explicit_editorial_pause(self):
        self._write_manifest({})
        with self.assertRaisesRegex(ValueError, "explicit editorial pause"):
            authored.validate_manifest(self.manifest)
        self.manifest.write_text(
            json.dumps({"schema_version": 1, "publication_status": "paused_pending_functional_review",
                        "pairs": {}}, ensure_ascii=False),
            encoding="utf-8",
        )
        self.assertEqual(authored.validate_manifest(self.manifest), {})


if __name__ == "__main__":
    unittest.main()
