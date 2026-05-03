# Training

This directory holds Web Agent Recoverability controller-training scaffolding: config templates, manifest builders, run-directory bootstrapping, and launcher glue.

## What this layer does

The training layer is intentionally lightweight. It does not hard-code a full trainer stack into the repository; instead it turns validated datasets into reproducible manifests and runnable shell commands.

## Main files

- `configs/controller_lora_template.json` — baseline LoRA/QLoRA-oriented config for a 7B/8B controller
- `scripts/prepare_training_manifest.py` — convert dataset paths + config into a single run manifest
- `scripts/bootstrap_run_dir.py` — create a reproducible run directory with manifest snapshots and metadata
- `scripts/render_hf_sft_command.py` — render a first HF/TRL-style SFT command from a manifest
- `scripts/launch_manifest.py` — one-shot helper that bootstraps a run dir, writes `train_command.sh`, and can optionally execute it

## Canonical committed run artifacts

The repository now keeps the larger public counterfactual run artifacts under version control:

- `generated/webvoyager_public_counterfactual_run_manifest.json`
- `generated/webvoyager_public_counterfactual_controller/`

The smaller smoke-test manifest / run directory is reproducible and therefore no longer committed by default.

## Typical usage

### Smoke-test launcher

```bash
make build-sample-manifest
make bootstrap-sample-run
```

### Public counterfactual launcher

```bash
make public-webvoyager-counterfactual-manifest
make launch-public-webvoyager-counterfactual-run
```

### Direct one-shot launch

```bash
python3 training/scripts/launch_manifest.py training/generated/webvoyager_public_counterfactual_run_manifest.json
```

This writes a runnable `train_command.sh` into the corresponding run directory. Add `--execute` only once the local training environment already has the required trainer stack installed.

## Current limitation

The repo has dry-run manifests and launch directories, but not a completed full fine-tuning result yet. The next milestone is to execute the counterfactual-controller run end to end and write the resulting metrics back into the paper.
