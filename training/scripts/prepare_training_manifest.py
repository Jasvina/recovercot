#!/usr/bin/env python3
"""Build a simple training run manifest for RecoverCoT controller experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-file", required=True)
    parser.add_argument("--dev-file", required=True)
    parser.add_argument("--test-file", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--metrics-file")
    args = parser.parse_args()

    manifest = {
        "run_name": args.run_name,
        "task": "recoverability_controller_sft",
        "data": {
            "train_file": args.train_file,
            "dev_file": args.dev_file,
            "test_file": args.test_file,
        },
        "config": args.config,
        "output_dir": args.output_dir,
        "expected_eval_metrics": args.metrics_file or "experiments/generated/sample_eval_metrics.json",
        "artifacts": {
            "best_checkpoint": f"{args.output_dir}/best_checkpoint",
            "predictions": f"{args.output_dir}/predictions.jsonl",
            "evaluation": f"{args.output_dir}/evaluation.json"
        }
    }
    Path(args.output).write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
