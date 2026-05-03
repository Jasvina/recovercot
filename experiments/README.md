# Experiments

This directory contains the Web Agent Recoverability offline data-construction pipeline: trajectory normalization, recoverability-state sampling, teacher-prompt rendering, bootstrap labeling, SFT conversion, and dataset statistics.

## Core workflow

The intended workflow is:

1. normalize trajectories into the Web Agent Recoverability format
2. sample intermediate states plus rollback checkpoints
3. optionally expand observed states into synthetic counterfactual stress-test states
4. render teacher requests
5. convert teacher outputs into recoverability records
6. build SFT training data and deterministic task-level splits
7. bootstrap a controller-training manifest

## Important subdirectories

- `examples/` — minimal smoke-test inputs and tiny raw examples for CI
- `generated/` — committed real experiment artifacts plus locally reproducible outputs
- `prompts/` — teacher-labeling prompt templates
- `schemas/` — JSON schema files for trajectory, state, and recoverability records
- `scripts/` — the actual preprocessing and labeling utilities

## Key scripts

- `scripts/adapt_benchmark_trajectories.py` — normalize benchmark-like raw traces and public WebVoyager result folders
- `scripts/sample_recoverability_states.py` — sample observed intermediate states from trajectories
- `scripts/augment_counterfactual_states.py` — expand observed states into synthetic counterfactual variants
- `scripts/render_teacher_requests.py` — render teacher prompts from sampled states
- `scripts/bootstrap_teacher_outputs.py` — create bootstrap silver labels when no strong teacher is available
- `scripts/build_recoverability_records.py` — merge states with teacher outputs into validated records
- `scripts/build_sft_training_data.py` — convert states + labels into chat-style SFT JSONL
- `scripts/split_recoverability_dataset.py` — deterministic task-level train/dev/test split utility
- `scripts/dataset_stats.py` — summarize trajectories, states, labels, or teacher-request prompts
- `scripts/build_webarena_verified_states.py` — convert WebArena-Verified task logs into sampled recoverability states
- `scripts/summarize_webarena_verified_logs.py` — summarize `agent_response.json` + `network.har` task logs from WebArena-Verified
- `scripts/validate_*.py` — stdlib-only JSONL validators

## Canonical committed artifacts

The repo now keeps the more informative public / counterfactual artifacts under version control, including:

- `generated/webvoyager_public_examples_normalized.jsonl`
- `generated/webvoyager_public_examples_states.jsonl`
- `generated/webvoyager_public_example_teacher_requests.jsonl`
- `generated/webvoyager_public_counterfactual_states.jsonl`
- `generated/webvoyager_public_counterfactual_recoverability_records.jsonl`
- `generated/webvoyager_public_counterfactual_sft_records.jsonl`
- `generated/webvoyager_public_counterfactual_sft_splits/`
- `generated/webvoyager_public_counterfactual_*_stats.json`

Toy smoke-test outputs such as `generated/sample_*` are intentionally not committed anymore; regenerate them locally when needed.

## Smoke-test run

```bash
make validate-sample
make sample-pipeline
make build-sample-records
make eval-sample
make build-sample-sft
make build-sample-manifest
make bootstrap-sample-run
```

## Public WebVoyager observed slice

```bash
make public-webvoyager-examples
```

This imports the official public WebVoyager example result folders, validates the normalized trajectories, samples recoverability states, builds task-level splits, and renders teacher prompts.

## Expanded counterfactual slice

```bash
make public-webvoyager-counterfactual-states
make public-webvoyager-counterfactual-labels
make public-webvoyager-counterfactual-manifest
make launch-public-webvoyager-counterfactual-run
```

This produces the current larger experimental slice used for controller-training dry runs:

- `167` total states
- `41` observed states
- `126` synthetic counterfactual states
- task-grouped SFT split: `93 / 21 / 53`

## Current caveat

The expanded counterfactual dataset is already useful for pipeline stress testing and first controller-training runs, but the labels are still bootstrap silver labels rather than final strong-teacher annotations.

## WebArena-Verified task-log summary

```bash
python3 experiments/scripts/summarize_webarena_verified_logs.py \
  $HOME/code/_external/webarena-verified/examples/agent_logs/demo \
  --output experiments/generated/webarena_verified_demo_log_summary.jsonl
```

This produces compact per-task summaries from `agent_response.json` and `network.har`, which is useful before adding a full recoverability-state adapter for the newer WebArena-Verified log format.

## WebArena-Verified sampled states

```bash
python3 experiments/scripts/build_webarena_verified_states.py \
  $HOME/code/_external/webarena-verified/examples/agent_logs/demo \
  --task-json $HOME/code/_external/webarena-verified/assets/dataset/webarena-verified.json \
  --output experiments/generated/webarena_verified_demo_states.jsonl
```

The resulting JSONL already conforms to the repository's sampled-state schema and can flow into `render_teacher_requests.py`, `bootstrap_teacher_outputs.py`, and `build_recoverability_records.py`.

To continue through the existing bootstrap path:

```bash
make webarena-verified-demo-summary REF_ROOT=$HOME/code/_external
make webarena-verified-demo-states REF_ROOT=$HOME/code/_external
make webarena-verified-demo-labels
```
