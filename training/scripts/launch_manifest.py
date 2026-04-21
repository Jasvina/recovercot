#!/usr/bin/env python3
"""Bootstrap and optionally launch a RecoverCoT training run from a manifest."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest_json")
    parser.add_argument(
        "--run-dir",
        help="directory for manifest snapshots and rendered command; defaults to training/generated/<run_name>",
    )
    parser.add_argument(
        "--command-output",
        help="path to write the rendered training command; defaults to <run-dir>/train_command.sh",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="execute the rendered training shell script after bootstrapping",
    )
    parser.add_argument(
        "--skip-bootstrap",
        action="store_true",
        help="skip run-directory bootstrapping and only render/optionally execute the command",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    manifest_path = Path(args.manifest_json).resolve()
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")

    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_name = manifest.get("run_name", "recovercot_run")
    run_dir = Path(args.run_dir) if args.run_dir else script_dir.parent / "generated" / run_name
    run_dir = run_dir.resolve()
    command_output = Path(args.command_output) if args.command_output else run_dir / "train_command.sh"
    command_output = command_output.resolve()
    command_output.parent.mkdir(parents=True, exist_ok=True)

    if not args.skip_bootstrap:
        run_step(
            [
                sys.executable,
                str(script_dir / "bootstrap_run_dir.py"),
                str(manifest_path),
                "--run-dir",
                str(run_dir),
            ]
        )

    run_step(
        [
            sys.executable,
            str(script_dir / "render_hf_sft_command.py"),
            str(manifest_path),
            "--output",
            str(command_output),
        ]
    )
    command_output.chmod(0o755)

    if args.execute:
        run_step(["bash", str(command_output)])

    print(command_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
