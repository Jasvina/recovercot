# Roadmap and Optimization Notes

This document records the current state of the Web Agent Recoverability repository after the cleanup / README refresh / experiment expansion pass, plus concrete next optimization directions.

## Current Snapshot

As of `2026-04-21 11:41:14 +0800`, this repository contains:

- a cleaned project structure with reproducible toy smoke-test outputs removed from version control;
- a refreshed GitHub homepage README with project framing, quick-start commands, current stats, and limitations;
- a compiled ACL/EMNLP-style paper draft source in `paper/main.tex`;
- a public WebVoyager observed trajectory/state slice;
- a larger synthetic counterfactual recoverability slice built from the observed public WebVoyager states;
- validation targets for both smoke-test outputs and committed public/counterfactual artifacts;
- dry-run training manifests and commands for the expanded counterfactual controller run.

## Current Data Artifacts

### Public WebVoyager Observed Slice

- Source: public WebVoyager example result folders under the local reference clone
- Trajectories: `15`
- Sampled states: `41`
- State split: `23 / 5 / 13` train/dev/test by task id
- Teacher requests: `41`
- Approximate teacher-request prompt budget: `62.6k` tokens

Important files:

- `experiments/generated/webvoyager_public_examples_normalized.jsonl`
- `experiments/generated/webvoyager_public_examples_states.jsonl`
- `experiments/generated/webvoyager_public_example_teacher_requests.jsonl`
- `experiments/generated/webvoyager_public_examples_state_stats.json`

### Expanded Counterfactual Slice

- Total states: `167`
- Observed states: `41`
- Synthetic counterfactual states: `126`
- Perturbation types:
  - `misleading_guidance`: `11`
  - `wrong_branch`: `37`
  - `repeated_failure`: `37`
  - `budget_pressure`: `41`
- SFT split: `93 / 21 / 53` train/dev/test by task id
- Teacher requests: `167`
- Approximate teacher-request prompt budget: `265k` tokens

Bootstrap label distribution:

- Recoverability:
  - `recoverable`: `22`
  - `weakly_recoverable`: `130`
  - `irrecoverable`: `15`
- Decision:
  - `continue`: `45`
  - `branch`: `11`
  - `rollback`: `96`
  - `restart`: `15`

Important files:

- `experiments/generated/webvoyager_public_counterfactual_states.jsonl`
- `experiments/generated/webvoyager_public_counterfactual_recoverability_records.jsonl`
- `experiments/generated/webvoyager_public_counterfactual_sft_records.jsonl`
- `experiments/generated/webvoyager_public_counterfactual_sft_splits/`
- `training/generated/webvoyager_public_counterfactual_run_manifest.json`
- `training/generated/webvoyager_public_counterfactual_controller/train_command.sh`

## Completed Cleanup

- Removed committed toy smoke-test outputs from `experiments/generated/`.
- Removed committed toy run manifests and sample run directories from `training/`.
- Kept smoke-test generation available through `make` targets and CI.
- Added `.gitignore` rules so regenerated toy/sample artifacts do not pollute `git status`.
- Extended `make clean` to remove reproducible local artifacts.
- Added `make validate-committed-artifacts` for checked-in public/counterfactual artifacts.

## Validation Already Run

The following checks have been run locally in this pass:

```bash
make validate-sample sample-pipeline build-sample-records eval-sample build-sample-sft benchmark-samples build-sample-manifest bootstrap-sample-run validate-committed-artifacts
python3 -m py_compile experiments/scripts/*.py training/scripts/*.py
make paper
make clean
```

Observed status:

- sample pipeline: passed
- benchmark-like smoke adapters: passed
- committed public/counterfactual artifact validation: passed
- Python syntax compilation: passed
- paper compilation with `tectonic`: passed, with layout warnings only
- cleanup target: passed after fixing directory removal for sample outputs

## Near-Term Optimization Plan

### 1. Broaden Real Benchmark Ingestion

Goal: reduce reliance on synthetic perturbations and make the paper stronger.

Planned work:

- add WebArena / WebArena-Verified trajectory-log importers where task logs or trace packages are available;
- promote the new WebArena-Verified task-log summary path (`agent_response.json` + `network.har`) into a full recoverability-state adapter;
- add Mind2Web raw-data importer once full local dataset files are available;
- support external agent logs with a generic JSONL adapter so other runs can be converted into Web Agent Recoverability trajectories;
- add dataset cards for each imported benchmark slice.

### 2. Upgrade Bootstrap Labels to Strong Teacher Labels

Goal: make recoverability supervision defensible for the final paper.

Planned work:

- run the rendered teacher requests through a strong teacher model;
- add response validation / retry logic for invalid JSON;
- compare bootstrap labels against strong-teacher labels to estimate disagreement;
- add human spot checks for a small balanced sample of continue / branch / rollback / restart cases;
- keep the same schema so downstream training remains stable.

### 3. Improve Counterfactual Perturbation Quality

Goal: make synthetic states less templated and more realistic.

Planned work:

- derive wrong-branch variants from actual alternative actions when available;
- generate site-aware perturbations instead of generic text prefixes;
- add harder cases where rollback target selection is non-trivial;
- balance perturbation types so branch/restart are not underrepresented;
- include ablations with and without synthetic perturbations.

### 4. Execute Controller Training

Goal: move from data pipeline to empirical results.

Planned work:

- install/verify the local trainer stack for the rendered `trl.sft_trainer` command;
- run a small LoRA controller job on the expanded counterfactual split;
- export predictions on dev/test splits;
- compute recoverability accuracy, decision accuracy, rollback precision, unnecessary rollback rate, and rollback-target accuracy;
- write the first real result row into `paper/main.tex`.

### 5. Strengthen Evaluation

Goal: ensure EMNLP reviewers can see that Web Agent Recoverability measures recovery behavior directly.

Planned work:

- add per-perturbation evaluation breakdowns;
- add calibration metrics for recoverability probability / confidence;
- add case-study extraction for representative continue, branch, rollback, and restart predictions;
- add an online replay or live-agent pilot if environment access is stable;
- compare against scalar reward / simple rollback baselines using the same state split.

### 6. Paper-Writing Improvements

Goal: convert the repository from scaffold to submission-ready paper.

Planned work:

- replace placeholder result tables with actual metrics;
- add a dataset-construction table for observed vs counterfactual slices;
- add a cost table for teacher prompt counts and approximate token budgets;
- add qualitative case studies with short, anonymized trajectory summaries;
- tighten limitations around synthetic labels and environment drift.

## Decision Notes

- The expanded counterfactual data is useful for stress testing and first controller training, but it should be described as silver supervision until strong-teacher labeling is added.
- The repository now tracks informative public/counterfactual artifacts, while keeping toy outputs reproducible but untracked.
- The next highest-value research step is not more scaffolding; it is either stronger labels or a first actual fine-tuning/evaluation run.
