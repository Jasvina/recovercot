#!/usr/bin/env python3
"""Adapt benchmark-like raw web-agent traces into RecoverCoT trajectory records."""

from __future__ import annotations

import argparse
import json
import re
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


def load_message_list(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"expected message list in {path}")
    return data


def flatten_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                elif item.get("type") == "image_url":
                    parts.append("[image]")
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def parse_instruction_and_site(text: str, fallback_task_id: str) -> tuple[str, str]:
    task_match = re.search(r"Now given a task:\s*(.*?)\s*Please interact with", text, re.DOTALL)
    url_match = re.search(r"(https?://[^\s]+)", text)
    instruction = task_match.group(1).strip() if task_match else fallback_task_id
    site = url_match.group(1).strip().rstrip(".") if url_match else "unknown_site"
    return instruction, site


def parse_webvoyager_action(text: str) -> tuple[str, str, Any]:
    action_match = re.search(r"Action:\s*(.+)", text, re.DOTALL)
    action_text = action_match.group(1).strip() if action_match else text.strip()
    if action_text.startswith("Click"):
        return "click", "click", action_text
    if action_text.startswith("Type"):
        return "type", "type", action_text
    if action_text.startswith("Scroll"):
        return "scroll", "scroll", action_text
    if action_text.startswith("Wait"):
        return "wait", "wait", action_text
    if action_text.startswith("GoBack"):
        return "goback", "goback", action_text
    if action_text.startswith("Google"):
        return "google", "google", action_text
    if action_text.startswith("ANSWER"):
        value = action_text.split(";", 1)[1].strip() if ";" in action_text else action_text
        return "answer", "answer", value
    return "other", "other", action_text


def infer_tags(action_type: str, action_payload: Any) -> list[str]:
    tags = ["webvoyager_trace"]
    if action_type in {"click", "type", "goback", "google"}:
        tags.append("page_transition")
    if action_type == "scroll":
        tags.append("scroll")
    if action_type == "type":
        tags.append("search_submit")
    if action_type == "answer":
        tags.append("answer_step")
    if isinstance(action_payload, str) and "wrong" in action_payload.lower():
        tags.append("error_signal")
    return tags


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


def adapt_webvoyager_results_dir(input_dir: Path) -> dict[str, Any]:
    messages = load_message_list(input_dir / "interact_messages.json")
    task_id = input_dir.name
    first_user = next((m for m in messages if m.get("role") == "user"), {})
    instruction, site = parse_instruction_and_site(flatten_content(first_user.get("content", "")), task_id)

    steps = []
    previous_user_text = flatten_content(first_user.get("content", ""))
    for message in messages[2:]:
        role = message.get("role")
        content_text = flatten_content(message.get("content", ""))
        if role == "user":
            previous_user_text = content_text
            continue
        if role != "assistant":
            continue
        action_type, action_name, action_value = parse_webvoyager_action(content_text)
        steps.append(
            {
                "step": len(steps) + 1,
                "url": site,
                "action_type": action_type,
                "action": action_name,
                "target": str(action_value)[:200] or action_name,
                "value": action_value if isinstance(action_value, str) else None,
                "observation": previous_user_text[:4000] or "Observation omitted.",
                "tags": infer_tags(action_type, action_value),
                "checkpoint": action_type in {"click", "type", "goback", "google", "answer"},
            }
        )
    success = bool(steps and steps[-1]["action_type"] == "answer")
    return {
        "task_id": task_id,
        "instruction": instruction,
        "site": site,
        "success": success,
        "max_steps": max(len(steps), 1),
        "steps": steps,
    }


def adapt_webvoyager_results_root(root_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for child in sorted(root_dir.iterdir()):
        if child.is_dir() and (child / "interact_messages.json").exists():
            rows.append(adapt_webvoyager_results_dir(child))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument(
        "--format",
        required=True,
        choices=[
            "webvoyager_like",
            "mind2web_like",
            "mind2web",
            "webvoyager_results_dir",
            "webvoyager_results_root",
        ],
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input_path)
    if args.format == "webvoyager_results_dir":
        rows = [adapt_webvoyager_results_dir(input_path)]
    elif args.format == "webvoyager_results_root":
        rows = adapt_webvoyager_results_root(input_path)
    else:
        raws = load_objects(input_path)
        adapter = adapt_webvoyager_like if args.format == "webvoyager_like" else adapt_mind2web_like
        rows = [adapter(raw) for raw in raws]
    text = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else "")
    Path(args.output).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
