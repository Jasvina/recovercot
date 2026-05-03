import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "experiments" / "scripts" / "adapt_benchmark_trajectories.py"
spec = importlib.util.spec_from_file_location("adapt_benchmark_trajectories", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class AdaptWebarenaRenderArchiveTest(unittest.TestCase):
    def test_returns_normalized_row_for_webarena_render_archive(self) -> None:
        html = """
        <html>
          <body>
            <h3 class="url"><a href="https://example.test/start">URL: https://example.test/start</a></h3>
            <div class="state_obv"><pre>Initial page state</pre><div></div>
            <div class="raw_parsed_prediction"><pre>click [12]</pre></div>
            <div class="parsed_action"><pre>type [7] [search term] [1]</pre></div>
          </body>
        </html>
        """

        config = [
            {
                "task_id": 7,
                "intent": "Find the archived item",
                "sites": ["shopping_admin"],
                "start_url": "https://fallback.example",
                "max_steps": 4,
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            archive_path = tmp_path / "renders.zip"
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with zipfile.ZipFile(archive_path, "w") as zf:
                zf.writestr("session/render_7.html", html)
                zf.writestr("session/merged_log.txt", "[Result] session/render_7.html (PASS)\n")

            rows = module.adapt_webarena_render_archive(archive_path, config_path)

        self.assertEqual(
            rows,
            [
                {
                    "task_id": "7",
                    "instruction": "Find the archived item",
                    "site": "shopping_admin",
                    "success": True,
                    "max_steps": 4,
                    "steps": [
                        {
                            "step": 1,
                            "url": "https://example.test/start",
                            "action_type": "type",
                            "action": "type",
                            "target": "type [7] [search term] [1]",
                            "value": "type [7] [search term] [1]",
                            "observation": "Initial page state",
                            "tags": ["webarena_trace", "page_transition", "search_submit"],
                            "checkpoint": True,
                        }
                    ],
                }
            ],
        )

    def test_defaults_max_steps_when_config_value_is_null(self) -> None:
        html = """
        <html>
          <body>
            <h3 class="url"><a href="https://example.test/page">URL: https://example.test/page</a></h3>
            <div class="state_obv"><pre>Observed state</pre><div></div>
            <div class="raw_parsed_prediction"><pre>go_forward</pre></div>
            <div class="parsed_action"><pre>go_forward</pre></div>
          </body>
        </html>
        """

        config = [
            {
                "task_id": 3,
                "intent": "Advance to the next page",
                "sites": ["reddit"],
                "max_steps": None,
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            archive_path = tmp_path / "renders.zip"
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with zipfile.ZipFile(archive_path, "w") as zf:
                zf.writestr("render_3.html", html)
                zf.writestr("merge_log.txt", "[Result] render_3.html (PASS)\n")

            rows = module.adapt_webarena_render_archive(archive_path, config_path)

        self.assertEqual(rows[0]["max_steps"], 1)
        self.assertEqual(rows[0]["steps"][0]["action_type"], "goforward")
        self.assertTrue(rows[0]["steps"][0]["checkpoint"])

    def test_raises_on_mismatched_render_sections(self) -> None:
        html = """
        <html>
          <body>
            <h3 class="url"><a href="https://example.test/start">URL: https://example.test/start</a></h3>
            <h3 class="url"><a href="https://example.test/extra">URL: https://example.test/extra</a></h3>
            <div class="state_obv"><pre>Initial page state</pre><div></div>
            <div class="raw_parsed_prediction"><pre>click [12]</pre></div>
            <div class="parsed_action"><pre>click [12]</pre></div>
          </body>
        </html>
        """

        config = [{"task_id": 11, "intent": "Broken render", "sites": ["shopping_admin"]}]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            archive_path = tmp_path / "renders.zip"
            config_path = tmp_path / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with zipfile.ZipFile(archive_path, "w") as zf:
                zf.writestr("render_11.html", html)
                zf.writestr("merged_log.txt", "[Result] render_11.html (PASS)\n")

            with self.assertRaisesRegex(ValueError, "mismatched WebArena render sections"):
                module.adapt_webarena_render_archive(archive_path, config_path)


if __name__ == "__main__":
    unittest.main()
