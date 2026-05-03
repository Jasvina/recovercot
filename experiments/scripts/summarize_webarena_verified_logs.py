#!/usr/bin/env python3
"""Summarize WebArena-Verified task logs into compact JSONL records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_site_host(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or parsed.path or "unknown_host"


def summarize_har_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    host_counts: dict[str, int] = {}
    method_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    interesting_requests: list[dict[str, Any]] = []

    for entry in entries:
        request = entry.get("request", {})
        response = entry.get("response", {})
        url = str(request.get("url", ""))
        method = str(request.get("method", "UNKNOWN"))
        status = str(response.get("status", "unknown"))
        host = normalize_site_host(url)

        host_counts[host] = host_counts.get(host, 0) + 1
        method_counts[method] = method_counts.get(method, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

        if len(interesting_requests) < 20:
            interesting_requests.append(
                {
                    "method": method,
                    "status": response.get("status"),
                    "url": url,
                    "mime_type": response.get("content", {}).get("mimeType"),
                }
            )

    top_hosts = [[host, count] for host, count in sorted(host_counts.items(), key=lambda item: (-item[1], item[0]))[:10]]
    return {
        "request_count": len(entries),
        "host_breakdown": top_hosts,
        "method_breakdown": method_counts,
        "status_breakdown": status_counts,
        "sample_requests": interesting_requests,
    }


def summarize_task_dir(task_dir: Path) -> dict[str, Any]:
    task_id = int(task_dir.name)
    agent_response = load_json(task_dir / "agent_response.json")
    har = load_json(task_dir / "network.har")
    entries = list(har.get("log", {}).get("entries", []))

    return {
        "task_id": task_id,
        "task_type": agent_response.get("task_type"),
        "status": agent_response.get("status"),
        "retrieved_data_count": len(agent_response.get("retrieved_data") or []),
        "has_error_details": agent_response.get("error_details") is not None,
        "network_summary": summarize_har_entries(entries),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs_root", help="directory containing per-task subdirectories with agent_response.json and network.har")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    logs_root = Path(args.logs_root)
    rows = []
    for child in sorted(logs_root.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "agent_response.json").exists():
            continue
        if not (child / "network.har").exists():
            continue
        rows.append(summarize_task_dir(child))

    text = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else "")
    Path(args.output).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
