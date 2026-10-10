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
import title_worklist as inventory


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
        self.assertGreaterEqual(len(pairs), 1914)
        self.assertEqual(len({t for v in pairs.values() for t in v.values()}), 2 * len(pairs))
        self.assertIn("Полный размер для концерта", pairs["kontrabas-chetyre-chetverti-v-arendu"]["n0"])
        self.assertIn("период подготовки", pairs["skripka-na-konkurs-v-arendu"]["n0"])
        self.assertNotIn("Сверьте мензуру", pairs["kontrabas-chetyre-chetverti-v-arendu"]["n0"])
        self.assertIn("Клавиатура и дыхание", pairs["melodika-vzroslomu-nachinayuschemu"]["n0"])
        self.assertIn("полного состава", pairs["instrumenty-dlya-studencheskogo-kamernogo-orkestra"]["n0"])
        self.assertIn("Рояль", pairs["instrumenty-dlya-fortepiannogo-kvinteta"]["n0"])
        self.assertIn("цифровой звук", pairs["instrument-esli-slishkom-gromko-dlya-doma"]["n1"])
        self.assertIn("Траверсо", pairs["traverso-dlya-pervogo-opyta"]["n0"])
        self.assertIn("Барочные инструменты", pairs["barochnye-instrumenty-dlya-opery"]["n0"])
        self.assertIn("Басовый усилитель", pairs["basovyy-usilitel-dlya-kontserta"]["n0"])
        self.assertIn("Клавишные по райдеру", pairs["scenicheskie-klavishnye-po-rayderu"]["n1"])
        self.assertIn("Бэклайн для фестиваля", pairs["backline-dlya-festivalya"]["n0"])
        self.assertIn("Yamaha YSV104", pairs["yamaha-ysv104-v-arendu"]["n0"])
        self.assertIn("Nord Grand 2", pairs["nord-grand-2-v-arendu"]["n1"])
        self.assertIn("Барабанная установка", pairs["barabannaya-ustanovka-dlya-studii"]["n0"])
        self.assertIn("Steinway D-274", pairs["steinway-d274-v-arendu"]["n0"])
        self.assertIn("Yamaha YTR-8335RS", pairs["yamaha-ytr8335rs-v-arendu"]["n1"])
        self.assertIn("Roland TR-808", pairs["roland-tr808-v-arendu"]["n0"])
        self.assertIn("БалалайкерЪ Студент Оптимум", pairs["balalayker-student-optimum-v-arendu"]["n0"])
        self.assertIn("Gemeinhardt 2SPCH", pairs["gemeinhardt-2spch-v-arendu"]["n0"])
        self.assertIn("Полупедаль цифрового пианино", pairs["cifrovoe-pianino-s-polupedalyu"]["n1"])
        self.assertIn("Контрабасовый смычок", pairs["kontrabasovye-smychki"]["n0"])
        self.assertIn("SONOR First Beat", pairs["sonor-first-beat-v-arendu"]["n0"])
        self.assertIn("Jupiter JTS700", pairs["jupiter-jts700-v-arendu"]["n1"])
        self.assertIn("FM-синтезатор", pairs["fm-sintezator"]["n0"])
        self.assertIn("Кора", pairs["kora"]["n1"])
        self.assertIn("Рояль для съёмки", pairs["royal-dlya-semki"]["n0"])
        self.assertIn("Дудук", pairs["duduk-dlya-saundtreka"]["n0"])
        self.assertIn("Korg minilogue xd", pairs["korg-minilogue-xd-v-arendu"]["n0"])
        self.assertIn("Балалайка-контрабас", pairs["balalayka-kontrabas"]["n0"])
        self.assertIn("Yamaha YFL-372", pairs["yamaha-yfl372-v-arendu"]["n0"])
        self.assertIn("Arcata Gasparo", pairs["arcata-gasparo-v-arendu"]["n0"])
        self.assertIn("Goronok Каденция", pairs["goronok-kadentsiya-kontrabas-v-arendu"]["n0"])
        self.assertIn("Fender CC-60S", pairs["fender-cc60s-v-arendu"]["n0"])
        self.assertIn("Yamaha YSL-350C", pairs["yamaha-ysl350c-v-arendu"]["n0"])
        self.assertIn("Hohner Special 20 C", pairs["hohner-special20-c-v-arendu"]["n0"])
        self.assertIn("Барочная скрипка", pairs["barochnaya-skripka"]["n0"])
        self.assertIn("траверсо", pairs["traverso"]["n0"].lower())
        self.assertIn("Жестовый контроллер", pairs["zhestovye-muzykalnye-kontrollery"]["n1"])
        self.assertIn("Pearl PL910C", pairs["pearl-pl910c-v-arendu"]["n0"])
        self.assertIn("Кастаньеты", pairs["kastanety"]["n0"])
        self.assertIn("Контрабас для джаза", pairs["kontrabas-dlya-dzhaza"]["n0"])
        self.assertIn("USB/MIDI", pairs["cifrovoe-pianino-s-usb-midi"]["n0"])
        self.assertIn("переезда", pairs["cifrovoe-pianino-dlya-pereezda"]["n0"])
        self.assertIn("Терменвокс для концерта", pairs["termenvoks-dlya-kontserta"]["n0"])
        self.assertIn("Рояль для конкурса", pairs["royal-dlya-konkursa"]["n0"])
        self.assertIn("Орган Hammond", pairs["hammond-organ"]["n0"])
        self.assertIn("Индийские музыкальные инструменты", pairs["indiyskie-muzykalnye-instrumenty"]["n0"])

    def test_only_gpt6_family_authors_public_title_copy(self):
        manifest = json.loads(authored.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["authoring_models"], ["GPT-6", "GPT-6.1"])
        self.assertEqual(manifest["python_role"], "literal_transfer_validation_coverage_only")
        self.assertGreaterEqual(len(manifest["pairs"]), 1914)

    def test_every_live_title_has_matching_source_evidence(self):
        titles = authored.validate_manifest(authored.DEFAULT_MANIFEST)
        evidence_path = ROOT / "content" / "title-editorial-evidence.json"
        evidence = inventory.load_review_records(evidence_path, ROOT)
        self.assertEqual(set(titles), set(evidence))
        for slug, pair in titles.items():
            self.assertEqual(set(evidence[slug]), {"n0", "n1"})
            for role in ("n0", "n1"):
                record = evidence[slug][role]
                self.assertEqual(record["decision"], pair[role])
                self.assertTrue(record["source_path"])
                self.assertGreater(len(record["source_quote"]), 12)

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
