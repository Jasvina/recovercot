import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "scripts"
    / "summarize_webarena_verified_logs.py"
)
spec = importlib.util.spec_from_file_location("summarize_webarena_verified_logs", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class SummarizeWebarenaVerifiedLogsTest(unittest.TestCase):
    def test_summarizes_agent_response_and_har(self) -> None:
        agent_response = {
            "task_type": "RETRIEVE",
            "status": "SUCCESS",
            "retrieved_data": [{"month": "Jan", "count": 12}],
            "error_details": None,
        }
        network_har = {
            "log": {
                "entries": [
                    {
                        "request": {"method": "GET", "url": "http://example.test/admin"},
                        "response": {"status": 302, "content": {"mimeType": "text/html"}},
                    },
                    {
                        "request": {"method": "POST", "url": "http://example.test/admin/api"},
                        "response": {"status": 200, "content": {"mimeType": "application/json"}},
                    },
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "108"
            task_dir.mkdir(parents=True)
            (task_dir / "agent_response.json").write_text(json.dumps(agent_response), encoding="utf-8")
            (task_dir / "network.har").write_text(json.dumps(network_har), encoding="utf-8")

            row = module.summarize_task_dir(task_dir)

        self.assertEqual(row["task_id"], 108)
        self.assertEqual(row["task_type"], "RETRIEVE")
        self.assertEqual(row["status"], "SUCCESS")
        self.assertEqual(row["retrieved_data_count"], 1)
        self.assertFalse(row["has_error_details"])
        self.assertEqual(row["network_summary"]["request_count"], 2)
        self.assertEqual(row["network_summary"]["method_breakdown"], {"GET": 1, "POST": 1})
        self.assertEqual(row["network_summary"]["status_breakdown"], {"302": 1, "200": 1})
        self.assertEqual(row["network_summary"]["host_breakdown"][0], ["example.test", 2])


if __name__ == "__main__":
    unittest.main()
