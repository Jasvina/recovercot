# Progress

Repository: `git@github.com:Jasvina/recovercot.git`
Canonical progress file: this document is the single root-level progress tracker.
Update rule: every meaningful repo update should add a timestamped entry here, plus refresh the current-progress and next-step sections.

## Current Progress

As of `2026-04-21 09:31:29 +0800`, the project has completed:

1. paper framing and ACL/EMNLP submission skeleton;
2. recoverability schemas, sample preprocessing, teacher-prompt rendering, label validation, and offline evaluation utilities;
3. toy end-to-end sample pipeline from trajectory -> sampled states -> teacher outputs -> recoverability records -> SFT JSONL;
4. benchmark-facing sample adapters for `webvoyager_like` and `mind2web_like` raw traces;
5. training config, run-manifest generation, and bootstrapped run-directory / command rendering glue.

What is still missing is real benchmark ingestion, real teacher labeling at scale, actual fine-tuning runs, and real result tables in the paper.

## Next Step Plan

Immediate next steps, in order:

1. replace benchmark-like toy adapters with real local dataset importers once raw benchmark files are available;
2. add a framework-specific training launcher wrapper around the generated run manifests;
3. produce non-degenerate train/dev/test splits from multi-task data;
4. run the first controller fine-tuning experiment and start writing actual result tables back into `paper/main.tex`.

## Timestamped Update Log

- `2026-04-20 18:00:05 +0800` - Initial RecoverCoT paper draft created and pushed (`29f9e6a`).
- `2026-04-20 20:14:46 +0800` - Draft strengthened with fuller method and experimental protocol (`cd52b21`).
- `2026-04-20 20:44:32 +0800` - Recoverability experiment scaffold added (`c58315e`).
- `2026-04-20 20:59:16 +0800` - Preprocessing and offline evaluation pipeline added (`6ef749f`).
- `2026-04-20 21:14:18 +0800` - Progress tracking and teacher-output to recoverability-record pipeline closed (`4ceba50`).
- `2026-04-21 09:27:42 +0800` - Benchmark adapters, stats utilities, dataset splits, and training manifests added (`1eb1eb5`).
- `2026-04-21 09:31:29 +0800` - Root-level canonical progress log added; training bootstrap and command-rendering work is being folded into the repo in this update (pending current commit).
