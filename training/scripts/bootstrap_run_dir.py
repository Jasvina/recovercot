#!/usr/bin/env python3
"""Create a reproducible run directory from a RecoverCoT training manifest."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest_json")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest_json)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = run_dir / "manifest.snapshot.json"
    snapshot_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_source": str(manifest_path),
        "run_name": manifest.get("run_name"),
        "task": manifest.get("task"),
    }
    (run_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    readme = f"""# Run Directory\n\nRun name: `{manifest.get('run_name')}`\n\nThis directory was bootstrapped from `{manifest_path}`.\nExpected artifacts:\n\n- best checkpoint: `{manifest.get('artifacts', {}).get('best_checkpoint')}`\n- predictions: `{manifest.get('artifacts', {}).get('predictions')}`\n- evaluation: `{manifest.get('artifacts', {}).get('evaluation')}`\n"""
    (run_dir / "README.md").write_text(readme, encoding="utf-8")
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
