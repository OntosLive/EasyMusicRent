"""Title coverage and functional evidence are tracked over every compiled address."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import title_worklist as inventory


class TitleWorklistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.site = self.base / "site"
        self.site.mkdir()
        self.slug = "skripka"
        self.source = self.base / "source.html"
        self.quote = "Размер инструмента определяется посадкой и длиной руки музыканта."
        self.source.write_text("<html><body><p>" + self.quote + "</p></body></html>", encoding="utf-8")
        self.authored = {
            "n0": "Скрипка в аренду | Проверьте размер по посадке и длине руки",
            "n1": "Скрипка и посадка | Размер определяет положение левой руки",
        }
        self.manifest = self.base / "manifest.json"
        self.reviews = self.base / "reviews.json"
        self._manifest({"skripka": self.authored})
        self._reviews({"skripka": {
            role: {"source_path": "source.html", "source_quote": self.quote,
                   "decision": "Посадка и длина руки влияют на выбор размера.",
                   "next_action": "Проверить постановку и выбрать соответствующий размер."}
            for role in ("n0", "n1")
        }})
        for path,title in [
            ("skripka/index.html",self.authored["n0"]),
            ("details/skripka/index.html",self.authored["n1"]),
            ("usloviya/srok-arendy/index.html","Срок аренды")
        ]:
            target = self.site / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("<html><head><title>"+title+"</title></head><body>Содержание</body></html>",
                              encoding="utf-8")
        self.report = {
            "conditions": 1,
            "pages": [{
                "slug": "skripka", "entry_title": "Аренда скрипки",
                "editorial_title": "Скрипка", "source": "source.html", "parent": "",
            }]
        }

    def _manifest(self, pairs, *, paused=False):
        self.manifest.write_text(json.dumps({
            "schema_version": 1,
            "publication_status": "paused_pending_functional_review" if paused else "model_reviewed_pilot",
            "pairs": pairs
        }, ensure_ascii=False), encoding="utf-8")

    def _reviews(self, reviews):
        self.reviews.write_text(json.dumps({"schema_version": 1, "reviews": reviews},
                                           ensure_ascii=False), encoding="utf-8")

    def run_inventory(self):
        return inventory.build_worklist(self.report, self.site, self.manifest,
                                        self.reviews, self.base)

    def test_complete_coverage_and_role_separation(self):
        result = self.run_inventory()
        stats = result["summary"]
        self.assertEqual((stats["source_topics"],stats["paired_titles"],
                          stats["conditions"],stats["total_html_titles"]), (1,2,1,3))
        self.assertEqual((stats["model_reviewed_titles"],stats["pending_all_titles"]), (2,1))
        self.assertEqual([r["role"] for r in result["records"]],["n0","n1","condition"])
        self.assertEqual(result["records"][0]["functional_next_action"],
                         "Проверить постановку и выбрать соответствующий размер.")
        self.assertFalse(stats["mechanically_generated_title_wording"])

    def test_unsupported_fragment_rejects_publication_audit(self):
        contents=json.loads(self.reviews.read_text(encoding="utf-8"))
        contents["reviews"]["skripka"]["n0"]["source_quote"]="Подтверждение, которого нет в содержимом документа."
        self._reviews(contents["reviews"])
        with self.assertRaisesRegex(ValueError, "evidence fragment not found"):
            self.run_inventory()

    def test_missing_independent_review_blocks_audit(self):
        self._reviews({})
        with self.assertRaisesRegex(ValueError, "Title / evidence topics differ"):
            self.run_inventory()

    def test_title_mismatch_is_not_ignored(self):
        (self.site / "skripka/index.html").write_text(
            "<html><head><title>Другая фраза</title></head><body></body></html>",encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "title differs"):
            self.run_inventory()

    def test_paused_manifest_still_lists_all_unreviewed_titles(self):
        self._manifest({}, paused=True)
        self._reviews({})
        result = self.run_inventory()
        self.assertEqual(result["summary"]["model_reviewed_titles"],0)
        self.assertEqual(result["summary"]["pending_all_titles"],3)


if __name__ == "__main__":
    unittest.main()
