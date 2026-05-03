import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "scripts"
    / "build_webarena_verified_states.py"
)
spec = importlib.util.spec_from_file_location("build_webarena_verified_states", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class BuildWebarenaVerifiedStatesTest(unittest.TestCase):
    def test_builds_valid_state_from_agent_response_and_har(self) -> None:
        task = {
            "task_id": 108,
            "sites": ["shopping_admin"],
            "intent": "Get monthly completed order counts.",
        }
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
                        "request": {"method": "GET", "url": "http://example.test/admin/dashboard"},
                        "response": {"status": 200, "content": {"mimeType": "text/html"}},
                    },
                    {
                        "request": {"method": "GET", "url": "http://example.test/admin/api/orders"},
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

            row = module.build_state_for_task(task, task_dir, history_window=4, checkpoint_limit=4)

        self.assertEqual(row["task_id"], "108")
        self.assertEqual(row["site"], "shopping_admin")
        self.assertEqual(row["state_origin"], "observed")
        self.assertTrue(row["source_success"])
        self.assertIn("retrieved_data_count=1", row["current_observation"])
        self.assertEqual(row["source_step"], 3)
        self.assertEqual(row["recent_history"][0]["action"], "get")
        self.assertEqual(row["checkpoint_candidates"][-1]["checkpoint_id"], "request_step_2")
        self.assertIn("task_type_retrieve", row["trigger_tags"])
        self.assertIn("answer_step", row["trigger_tags"])


if __name__ == "__main__":
    unittest.main()
