#!/usr/bin/env python3
"""Split RecoverCoT JSONL datasets by task id with deterministic hashing."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def bucket_for(task_id: str, train_ratio: float, dev_ratio: float) -> str:
    value = int(hashlib.md5(task_id.encode("utf-8")).hexdigest(), 16) % 10_000
    frac = value / 10_000.0
    if frac < train_ratio:
        return "train"
    if frac < train_ratio + dev_ratio:
        return "dev"
    return "test"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_jsonl")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--dev-ratio", type=float, default=0.1)
    parser.add_argument("--group-key", default="task_id")
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input_jsonl))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    buckets: dict[str, list[str]] = {"train": [], "dev": [], "test": []}
    for row in rows:
        group_value = row.get(args.group_key) or row.get("task_id") or row.get("id") or row.get("state_id")
        if not group_value:
            raise ValueError(f"row missing split key {args.group_key!r} and fallback ids")
        bucket = bucket_for(str(group_value), args.train_ratio, args.dev_ratio)
        buckets[bucket].append(json.dumps(row, ensure_ascii=True))
    for name, lines in buckets.items():
        text = "\n".join(lines) + ("\n" if lines else "")
        (out_dir / f"{name}.jsonl").write_text(text, encoding="utf-8")
    manifest = {name: len(lines) for name, lines in buckets.items()}
    manifest["group_key"] = args.group_key
    empty = [name for name, lines in buckets.items() if len(lines) == 0]
    if empty:
        manifest["warning"] = f"empty splits: {', '.join(empty)}; this is expected on tiny toy data but should be avoided for real runs"
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
