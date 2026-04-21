# RecoverCoT

![validate](https://github.com/Jasvina/recovercot/actions/workflows/validate.yml/badge.svg)

RecoverCoT is an EMNLP-style paper and experiment repository for:

> RecoverCoT: Counterfactual Recoverability Distillation for Robust Web Agents

The central idea is simple: before a web agent takes its next action, it should estimate whether the current state is still recoverable, whether it should continue / branch / rollback / restart, and which checkpoint is best if rollback is needed.

## Why this repository exists

Most web-agent work improves next-action prediction, reward modeling, reflection, or rollback mechanics. RecoverCoT targets a different control problem: explicit state-level recoverability. This repository packages three pieces together so the paper and experiments stay synchronized:

- an ACL/EMNLP paper draft in `paper/`
- a recoverability-data pipeline in `experiments/`
- controller-training manifests and launch glue in `training/`

## What is already implemented

The current repository can already run an end-to-end offline recoverability workflow:

1. normalize benchmark-style or public result traces into a shared trajectory format
2. sample high-value intermediate states plus rollback checkpoints
3. render teacher-labeling prompts for each state
4. build recoverability records and SFT data
5. split train/dev/test sets deterministically by task
6. render controller-training manifests and runnable trainer commands

## Current experiment snapshot

Committed experiment artifacts now cover a real public WebVoyager slice plus an expanded synthetic counterfactual stress test:

- observed public WebVoyager slice: `15` trajectories, `41` sampled states
- synthetic counterfactual expansion: `167` total states
- counterfactual state origins: `41` observed + `126` synthetic
- bootstrap label mix on the expanded set:
  - `45` continue
  - `11` branch
  - `96` rollback
  - `15` restart
- task-grouped SFT split on the expanded set: `93 / 21 / 53` train/dev/test examples
- rendered teacher-request budget for the expanded set: about `265k` approximate prompt tokens

These numbers are intentionally framed as pipeline and dataset status, not final paper claims.

## Quick start

### 1. Validate the lightweight smoke-test pipeline

```bash
make validate-sample
make sample-pipeline
make build-sample-records
make eval-sample
make build-sample-sft
make build-sample-manifest
make bootstrap-sample-run
```

### 2. Build the paper locally

```bash
make paper
```

### 3. Import and expand the public WebVoyager experiment slice

```bash
make fetch-public-refs
make public-webvoyager-examples
make public-webvoyager-counterfactual-states
make public-webvoyager-counterfactual-labels
make public-webvoyager-counterfactual-manifest
make launch-public-webvoyager-counterfactual-run
```

## Repository map

- `PROGRESS.md` — canonical root-level progress log with timestamps, current status, and next steps
- `ROADMAP.md` — current snapshot plus future optimization directions
- `paper/main.tex` — main EMNLP-style draft
- `paper/references.bib` — bibliography used by the draft
- `experiments/` — trajectory adapters, state samplers, prompt rendering, validators, label builders, and dataset stats
- `training/` — controller config templates, manifest builders, bootstrap run directories, and launch helpers
- `scripts/fetch_public_refs.sh` — local fetch/update helper for public reference repositories

## Tracked vs reproducible artifacts

To keep the repository clean, reproducible smoke-test outputs are no longer committed. The repo now tracks the more informative public WebVoyager and counterfactual experiment artifacts, while toy sample outputs can be regenerated on demand with the `make` targets above.

## Most useful paths

- paper draft: `paper/main.tex`
- progress tracker: `PROGRESS.md`
- public observed trajectories: `experiments/generated/webvoyager_public_examples_normalized.jsonl`
- public observed states: `experiments/generated/webvoyager_public_examples_states.jsonl`
- expanded counterfactual states: `experiments/generated/webvoyager_public_counterfactual_states.jsonl`
- expanded label stats: `experiments/generated/webvoyager_public_counterfactual_recoverability_stats.json`
- expanded run manifest: `training/generated/webvoyager_public_counterfactual_run_manifest.json`

## Current limitations

- WebArena / WebArena-Verified trajectory ingestion is not finished yet
- current large-scale labels are still bootstrap / silver labels rather than final strong-teacher labels
- no full fine-tuning run has been executed to completion inside this repository yet
- result tables in the paper are still templates and must be replaced with actual experiment numbers

## Near-term roadmap

1. add broader real benchmark ingestion beyond public WebVoyager examples
2. replace bootstrap counterfactual labels with stronger teacher judgments
3. run the first real controller fine-tuning job on the expanded split
4. write the first concrete result tables back into `paper/main.tex`

## Push / pull

```bash
git pull --ff-only origin main
git push -u origin main
```
