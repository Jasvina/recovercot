#!/usr/bin/env python3
"""Build sampled recoverability states from WebArena-Verified task logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


STATIC_EXTENSIONS = {
    ".css",
    ".js",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".ico",
    ".map",
}

STATIC_MIME_PREFIXES = (
    "image/",
    "font/",
)

STATIC_MIME_EXACT = {
    "text/css",
    "application/javascript",
    "text/javascript",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_target(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or "unknown_host"
    path = parsed.path or "/"
    return f"{host}{path}"


def is_static_asset(entry: dict[str, Any]) -> bool:
    request = entry.get("request", {})
    response = entry.get("response", {})
    url = str(request.get("url", ""))
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    mime_type = str(response.get("content", {}).get("mimeType", "")).split(";", 1)[0].strip().lower()

    if suffix in STATIC_EXTENSIONS:
        return True
    if parsed.path.startswith("/static/") or "/static/" in parsed.path:
        return True
    if mime_type in STATIC_MIME_EXACT:
        return True
    return any(mime_type.startswith(prefix) for prefix in STATIC_MIME_PREFIXES)


def entry_tags(entry: dict[str, Any], task_type: str, success: bool) -> list[str]:
    request = entry.get("request", {})
    response = entry.get("response", {})
    method = str(request.get("method", "GET")).upper()
    status = int(response.get("status", 0) or 0)
    mime_type = str(response.get("content", {}).get("mimeType", "")).split(";", 1)[0].strip().lower()

    tags = ["webarena_verified_log", "network_trace", f"task_type_{task_type.lower()}"]
    if method != "GET":
        tags.append("mutation_request")
    if status >= 300 and status < 400:
        tags.append("redirect")
    if status >= 400:
        tags.append("error_signal")
    if mime_type == "text/html":
        tags.append("html_response")
    if mime_type == "application/json":
        tags.append("json_response")
    if success:
        tags.append("answer_step")
    return tags


def filter_interesting_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    interesting = [entry for entry in entries if not is_static_asset(entry)]
    if interesting:
        return interesting
    return entries[-1:] if entries else []


def build_history_entry(step_idx: int, entry: dict[str, Any], task_type: str, success: bool) -> dict[str, Any]:
    request = entry.get("request", {})
    response = entry.get("response", {})
    url = str(request.get("url", ""))
    method = str(request.get("method", "GET")).upper()
    status = int(response.get("status", 0) or 0)
    mime_type = str(response.get("content", {}).get("mimeType", "")).split(";", 1)[0].strip().lower()
    return {
        "step": step_idx,
        "action": method.lower(),
        "target": normalize_target(url),
        "value": None,
        "observation": f"status={status} mime_type={mime_type or 'unknown'} url={url}",
        "tags": entry_tags(entry, task_type, success),
    }


def build_checkpoint_candidates(
    history_entries: list[dict[str, Any]],
    checkpoint_limit: int,
) -> list[dict[str, Any]]:
    checkpoints = []
    for item in history_entries:
        checkpoints.append(
            {
                "checkpoint_id": f"request_step_{item['step']}",
                "step": item["step"],
                "summary": item["observation"][:180],
            }
        )
    return checkpoints[-checkpoint_limit:]


def summarize_retrieved_data(agent_response: dict[str, Any]) -> str:
    retrieved = agent_response.get("retrieved_data")
    if not retrieved:
        return "retrieved_data=<empty>"
    preview = json.dumps(retrieved[:2], ensure_ascii=True)
    return f"retrieved_data_count={len(retrieved)} preview={preview}"


def build_state_for_task(
    task: dict[str, Any],
    task_dir: Path,
    history_window: int,
    checkpoint_limit: int,
) -> dict[str, Any]:
    agent_response = load_json(task_dir / "agent_response.json")
    har = load_json(task_dir / "network.har")
    task_type = str(agent_response.get("task_type", "UNKNOWN"))
    success = str(agent_response.get("status", "")).upper() == "SUCCESS"
    entries = list(har.get("log", {}).get("entries", []))
    interesting_entries = filter_interesting_entries(entries)
    if not interesting_entries:
        raise ValueError(f"no HAR entries available for task {task_dir.name}")

    history = [
        build_history_entry(idx + 1, entry, task_type, success)
        for idx, entry in enumerate(interesting_entries)
    ]
    current = history[-1]
    recent_history = history[max(0, len(history) - 1 - history_window) : -1]
    checkpoints = build_checkpoint_candidates(history[:-1], checkpoint_limit)
    current_url = str(interesting_entries[-1].get("request", {}).get("url", ""))
    if not current_url:
        current_url = f"http://{task.get('sites', ['unknown_site'])[0]}/"

    current_observation = (
        f"Task type={task_type}; status={agent_response.get('status')}; "
        f"{summarize_retrieved_data(agent_response)}; current_request={current['observation']}"
    )

    return {
        "task_id": str(task["task_id"]),
        "state_id": f"webarena_verified_task_{task['task_id']}_step_{current['step']}",
        "source_step": current["step"],
        "instruction": task.get("intent", f"task_{task['task_id']}"),
        "site": ",".join(task.get("sites", [])) or "unknown_site",
        "current_url": current_url,
        "current_observation": current_observation,
        "recent_history": recent_history,
        "checkpoint_candidates": checkpoints,
        "trigger_tags": current["tags"],
        "remaining_budget": 2 if success else 1,
        "source_success": success,
        "state_origin": "observed",
        "parent_state_id": None,
        "perturbation_type": None,
        "perturbation_note": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs_root", help="directory containing task log subdirectories")
    parser.add_argument("--task-json", required=True, help="path to webarena-verified task definition JSON")
    parser.add_argument("--output", required=True)
    parser.add_argument("--history-window", type=int, default=4)
    parser.add_argument("--checkpoint-limit", type=int, default=4)
    args = parser.parse_args()

    task_map = {int(task["task_id"]): task for task in load_json(Path(args.task_json))}
    logs_root = Path(args.logs_root)
    rows = []
    for child in sorted(logs_root.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "agent_response.json").exists() or not (child / "network.har").exists():
            continue
        task_id = int(child.name)
        task = task_map.get(task_id)
        if task is None:
            raise ValueError(f"task id {task_id} missing from task json")
        rows.append(build_state_for_task(task, child, args.history_window, args.checkpoint_limit))

    text = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else "")
    Path(args.output).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
