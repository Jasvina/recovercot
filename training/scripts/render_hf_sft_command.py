#!/usr/bin/env python3
"""Render a placeholder HF/TRL-style SFT command from a RecoverCoT manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest_json")
    parser.add_argument("--output")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest_json).read_text(encoding="utf-8"))
    config = json.loads(Path(manifest["config"]).read_text(encoding="utf-8"))

    command = f"""python -m trl.sft_trainer \\
  --model_name_or_path {config['model_name_or_path']} \\
  --train_file {manifest['data']['train_file']} \\
  --eval_file {manifest['data']['dev_file']} \\
  --output_dir {manifest['output_dir']} \\
  --per_device_train_batch_size {config['per_device_train_batch_size']} \\
  --gradient_accumulation_steps {config['gradient_accumulation_steps']} \\
  --learning_rate {config['learning_rate']} \\
  --num_train_epochs {config['num_train_epochs']} \\
  --max_seq_length {config['max_seq_length']} \\
  --logging_steps {config['logging_steps']} \\
  --lora_r {config['lora_rank']} \\
  --lora_alpha {config['lora_alpha']} \\
  --lora_dropout {config['lora_dropout']}
"""
    if args.output:
        Path(args.output).write_text(command, encoding="utf-8")
    print(command, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
