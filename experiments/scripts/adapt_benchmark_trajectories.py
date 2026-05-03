#!/usr/bin/env python3
"""Adapt benchmark-like raw web-agent traces into RecoverCoT trajectory records."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from html import unescape
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


def parse_render_log(text: str) -> dict[str, list[str]]:
    patterns = {
        "urls": r"<h3 class=['\"]url['\"]><a href=.*?>URL:\s*(.*?)</a></h3>",
        "observations": r"<div class=['\"]state_obv['\"]><pre>(.*?)</pre><div>",
        "raw_predictions": r"<div class=['\"]raw_parsed_prediction['\"][^>]*><pre>(.*?)</pre></div>",
        "parsed_actions": r"<div class=['\"]parsed_action['\"][^>]*><pre>(.*?)</pre></div>",
    }
    parsed: dict[str, list[str]] = {}
    for key, pattern in patterns.items():
        parsed[key] = [unescape(match).strip() for match in re.findall(pattern, text, re.DOTALL)]
    return parsed


def parse_webarena_action(text: str) -> tuple[str, str, str | None]:
    normalized = unescape(text).strip()
    if not normalized:
        return "other", "other", None

    action_word = normalized.split(maxsplit=1)[0].lower()
    if action_word == "click":
        return "click", "click", normalized
    if action_word == "type":
        return "type", "type", normalized
    if action_word == "hover":
        return "hover", "hover", normalized
    if action_word == "scroll":
        return "scroll", "scroll", normalized
    if action_word in {"go_back", "goback"}:
        return "goback", "goback", normalized
    if action_word == "goto":
        return "goto", "goto", normalized
    if action_word == "press":
        return "press", "press", normalized
    if action_word == "go_forward":
        return "goforward", "goforward", normalized
    if action_word == "new_tab":
        return "newtab", "newtab", normalized
    if action_word == "close_tab":
        return "closetab", "closetab", normalized
    if action_word == "page_focus":
        return "pagefocus", "pagefocus", normalized
    if action_word == "stop":
        return "stop", "stop", normalized
    return action_word, action_word, normalized


def infer_webarena_tags(action_type: str) -> list[str]:
    tags = ["webarena_trace"]
    if action_type in {
        "click",
        "type",
        "goback",
        "goto",
        "press",
        "stop",
        "goforward",
        "newtab",
        "closetab",
        "pagefocus",
    }:
        tags.append("page_transition")
    if action_type == "type":
        tags.append("search_submit")
    if action_type == "stop":
        tags.append("answer_step")
    return tags


def load_task_config_map(config_json: Path | None) -> dict[int, dict[str, Any]]:
    if config_json is None:
        return {}
    configs = load_objects(config_json)
    return {int(item["task_id"]): item for item in configs}


def load_webarena_success_map(root_dir: Path) -> dict[int, bool]:
    success_map: dict[int, bool] = {}
    log_files = [*root_dir.rglob("merged_log.txt"), *root_dir.rglob("merge_log.txt")]
    for log_file in log_files:
        for line in log_file.read_text(encoding="utf-8").splitlines():
            match = re.search(r"render_(\d+)\.html", line)
            result = re.search(r"\((PASS|FAIL)\)", line)
            if match and result:
                success_map[int(match.group(1))] = result.group(1) == "PASS"
    return success_map


def build_webarena_steps(parsed: dict[str, list[str]]) -> list[dict[str, Any]]:
    urls = parsed["urls"]
    observations = parsed["observations"]
    raw_predictions = parsed["raw_predictions"]
    parsed_actions = parsed["parsed_actions"]
    action_count = len(raw_predictions) if raw_predictions else len(parsed_actions)
    counts = {
        "urls": len(urls),
        "observations": len(observations),
        "actions": action_count,
    }
    nonzero_counts = {key: value for key, value in counts.items() if value > 0}
    if len(set(nonzero_counts.values())) > 1:
        raise ValueError(f"mismatched WebArena render sections: {counts}")
    step_count = min(len(urls), len(observations), action_count)

    steps: list[dict[str, Any]] = []
    for idx in range(step_count):
        action_text = parsed_actions[idx] if idx < len(parsed_actions) and parsed_actions[idx] else raw_predictions[idx]
        action_type, action_name, action_payload = parse_webarena_action(action_text)
        steps.append(
            {
                "step": idx + 1,
                "url": urls[idx],
                "action_type": action_type,
                "action": action_name,
                "target": action_payload or action_name,
                "value": action_payload if action_type == "type" else None,
                "observation": observations[idx],
                "tags": infer_webarena_tags(action_type),
                "checkpoint": action_type
                in {
                    "click",
                    "type",
                    "goback",
                    "goto",
                    "press",
                    "stop",
                    "goforward",
                    "newtab",
                    "closetab",
                    "pagefocus",
                },
            }
        )
    if not steps:
        raise ValueError(f"no aligned WebArena steps extracted: {counts}")
    return steps


def build_webarena_row(task_id: int, config: dict[str, Any], success: bool, parsed: dict[str, list[str]]) -> dict[str, Any]:
    steps = build_webarena_steps(parsed)
    raw_max_steps = config.get("max_steps")
    max_steps = int(raw_max_steps) if raw_max_steps is not None else max(len(steps), 1)
    return {
        "task_id": str(task_id),
        "instruction": config.get("intent", config.get("instruction", f"task_{task_id}")),
        "site": ",".join(config.get("sites", [])) or config.get("start_url", "unknown_site"),
        "success": success,
        "max_steps": max_steps,
        "steps": steps,
    }


def adapt_webarena_render_root(root_dir: Path, config_json: Path | None) -> list[dict[str, Any]]:
    configs = load_task_config_map(config_json)
    success_map = load_webarena_success_map(root_dir)
    rows = []
    render_files = sorted(root_dir.rglob("render_*.html"))
    if not render_files:
        raise ValueError(f"no render_*.html files found in {root_dir}")
    for render_file in render_files:
        task_id_match = re.search(r"render_(\d+)\.html$", render_file.name)
        if not task_id_match:
            continue
        task_id = int(task_id_match.group(1))
        config = configs.get(task_id, {})
        parsed = parse_render_log(render_file.read_text(encoding="utf-8"))
        rows.append(build_webarena_row(task_id, config, success_map.get(task_id, False), parsed))
    return rows


def adapt_webarena_render_archive(archive_path: Path, config_json: Path | None) -> list[dict[str, Any]]:
    if not archive_path.exists():
        raise FileNotFoundError(f"archive not found: {archive_path}")
    if archive_path.suffix != ".zip":
        raise ValueError(f"expected a .zip archive: {archive_path}")

    with zipfile.ZipFile(archive_path, "r") as zf:
        members = sorted(name for name in zf.namelist() if re.search(r"(^|/)render_\d+\.html$", name))
        if not members:
            raise ValueError(f"no render_*.html files found in {archive_path}")

        configs = load_task_config_map(config_json)
        success_map: dict[int, bool] = {}
        for name in zf.namelist():
            if name.endswith("merged_log.txt") or name.endswith("merge_log.txt"):
                for line in zf.read(name).decode("utf-8", errors="replace").splitlines():
                    match = re.search(r"render_(\d+)\.html", line)
                    result = re.search(r"\((PASS|FAIL)\)", line)
                    if match and result:
                        success_map[int(match.group(1))] = result.group(1) == "PASS"
                break

        rows = []
        for member in members:
            task_id_match = re.search(r"render_(\d+)\.html$", member)
            if not task_id_match:
                continue
            task_id = int(task_id_match.group(1))
            config = configs.get(task_id, {})
            parsed = parse_render_log(zf.read(member).decode("utf-8", errors="replace"))
            rows.append(build_webarena_row(task_id, config, success_map.get(task_id, False), parsed))
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
            "webarena_render_root",
            "webarena_render_archive",
        ],
    )
    parser.add_argument("--config-json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input_path)
    if args.format == "webvoyager_results_dir":
        rows = [adapt_webvoyager_results_dir(input_path)]
    elif args.format == "webvoyager_results_root":
        rows = adapt_webvoyager_results_root(input_path)
    elif args.format == "webarena_render_root":
        if not args.config_json:
            raise ValueError("--config-json is required for webarena_render_root")
        rows = adapt_webarena_render_root(input_path, Path(args.config_json))
    elif args.format == "webarena_render_archive":
        if not args.config_json:
            raise ValueError("--config-json is required for webarena_render_archive")
        rows = adapt_webarena_render_archive(input_path, Path(args.config_json))
    else:
        raws = load_objects(input_path)
        adapter = adapt_webvoyager_like if args.format == "webvoyager_like" else adapt_mind2web_like
        rows = [adapter(raw) for raw in raws]
    text = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else "")
    Path(args.output).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
