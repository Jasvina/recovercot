#!/usr/bin/env python3
"""Adapt benchmark-like raw web-agent traces into RecoverCoT trajectory records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_objects(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return data
    return [data]


def adapt_webvoyager_like(raw: dict[str, Any]) -> dict[str, Any]:
    steps = []
    for step in raw.get("trajectory", []):
        action = step.get("action", {})
        meta = step.get("meta", {})
        steps.append(
            {
                "step": int(step.get("step_id", len(steps) + 1)),
                "url": step.get("url", ""),
                "action_type": action.get("type", "unknown").lower(),
                "action": action.get("name", action.get("type", "unknown").lower()),
                "target": str(action.get("target", "")),
                "value": action.get("value"),
                "observation": step.get("observation", {}).get("text", ""),
                "tags": list(meta.get("tags", [])),
                "checkpoint": bool(meta.get("checkpoint", False)),
            }
        )
    return {
        "task_id": raw.get("task_id", "unknown_task"),
        "instruction": raw.get("instruction", ""),
        "site": raw.get("site", raw.get("website", "unknown_site")),
        "success": raw.get("status") == "success",
        "max_steps": int(raw.get("max_steps", max(len(steps), 1))),
        "steps": steps,
    }


def adapt_mind2web_like(raw: dict[str, Any]) -> dict[str, Any]:
    steps = []
    for idx, action in enumerate(raw.get("actions", []), start=1):
        op = action.get("operation", {})
        candidates = action.get("pos_candidates", [])
        primary = candidates[0] if candidates else {}
        target = primary.get("text") or primary.get("backend_node_id") or op.get("value") or "unknown_target"
        tags = list(action.get("tags", []))
        if op.get("op", "").upper() == "TYPE" and "search_submit" not in tags:
            tags.append("search_submit")
        steps.append(
            {
                "step": idx,
                "url": action.get("url", ""),
                "action_type": op.get("op", "unknown").lower(),
                "action": op.get("op", "unknown").lower(),
                "target": str(target),
                "value": op.get("value"),
                "observation": action.get("observation", ""),
                "tags": tags,
                "checkpoint": bool(action.get("checkpoint", False)),
            }
        )
    return {
        "task_id": raw.get("annotation_id", raw.get("task_id", "unknown_task")),
        "instruction": raw.get("confirmed_task", raw.get("instruction", "")),
        "site": raw.get("website", raw.get("site", "unknown_site")),
        "success": bool(raw.get("is_success", False)),
        "max_steps": max(len(steps), 1),
        "steps": steps,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("--format", required=True, choices=["webvoyager_like", "mind2web_like"])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    raws = load_objects(Path(args.input_path))
    adapter = adapt_webvoyager_like if args.format == "webvoyager_like" else adapt_mind2web_like
    rows = [adapter(raw) for raw in raws]
    text = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else "")
    Path(args.output).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
