# Progress

Repository: `git@github.com:Jasvina/recovercot.git`
Canonical progress file: this document is the single root-level progress tracker.
Update rule: every meaningful repo update should add a timestamped entry here, plus refresh the current-progress and next-step sections.
Companion planning file: see `ROADMAP.md` for the current snapshot plus future optimization directions.

## Current Progress

As of `2026-04-21 11:47:31 +0800`, the project has completed:

1. paper framing and ACL/EMNLP submission skeleton;
2. recoverability schemas, sample preprocessing, teacher-prompt rendering, label validation, and offline evaluation utilities;
3. toy end-to-end sample pipeline from trajectory -> sampled states -> teacher outputs -> recoverability records -> SFT JSONL;
4. benchmark-facing sample adapters for `webvoyager_like` and `mind2web_like` raw traces;
5. training config, run-manifest generation, bootstrapped run directories, and a one-shot manifest launcher for controller fine-tuning;
6. imported a non-trivial public WebVoyager example corpus from the official example result folders and produced real multi-task sampled-state splits;
7. generated a first real teacher-request bundle for the imported WebVoyager states: 41 prompts totaling about 62.6k approximate prompt tokens;
8. generated bootstrap silver labels, recoverability records, SFT data, and a dry-run training manifest for the public WebVoyager example slice (`23/5/13` train/dev/test states, `41` labeled states total);
9. bundled ACL style files in-repo and verified that `paper/main.tex` compiles successfully with `tectonic`;
10. synced the paper draft and training docs with the new public-example bootstrap path so the manuscript and runnable artifacts stay aligned;
11. cleaned the repository by removing committed toy/generated smoke-test outputs and ignored reproducible artifacts, while keeping the more informative public WebVoyager artifacts;
12. refreshed the GitHub homepage `README.md` into a clearer project landing page with current dataset stats, quick-start commands, roadmap, and limitations;
13. added a large counterfactual expansion pipeline over the public WebVoyager states: `167` total states (`41` observed + `126` synthetic), `265k` approximate teacher-prompt tokens, and a `93/21/53` train/dev/test split with continue/branch/rollback/restart labels;
14. recorded the current repository snapshot, validation status, and future optimization directions in the new root-level `ROADMAP.md` document.

What is still missing is broader benchmark ingestion, stronger teacher labeling beyond bootstrap heuristics, actual fine-tuning runs, and real result tables in the paper.

## Next Step Plan

Immediate next steps, in order:

1. add real importer coverage for additional benchmark outputs beyond WebVoyager public examples, especially WebArena/WebArena-Verified task logs;
2. replace the bootstrap counterfactual labels with stronger teacher judgments while preserving the same schema and split structure;
3. run the first actual controller fine-tuning job on the expanded counterfactual split and record training/eval artifacts back into the repo;
4. start writing concrete dataset statistics and first result-table entries back into `paper/main.tex`.

## Timestamped Update Log

- `2026-04-20 18:00:05 +0800` - Initial RecoverCoT paper draft created and pushed (`29f9e6a`).
- `2026-04-20 20:14:46 +0800` - Draft strengthened with fuller method and experimental protocol (`cd52b21`).
- `2026-04-20 20:44:32 +0800` - Recoverability experiment scaffold added (`c58315e`).
- `2026-04-20 20:59:16 +0800` - Preprocessing and offline evaluation pipeline added (`6ef749f`).
- `2026-04-20 21:14:18 +0800` - Progress tracking and teacher-output to recoverability-record pipeline closed (`4ceba50`).
- `2026-04-21 09:27:42 +0800` - Benchmark adapters, stats utilities, dataset splits, and training manifests added (`1eb1eb5`).
- `2026-04-21 09:31:29 +0800` - Root-level canonical progress log added; training bootstrap and command-rendering work was folded into the repo (`3d22b56`).
- `2026-04-21 09:45:30 +0800` - Public benchmark reference repos were cloned locally, and the repo now imports and splits real WebVoyager public example trajectories instead of relying only on toy examples (`e65f623`).
- `2026-04-21 11:11:24 +0800` - ACL style files were vendored locally, the paper now compiles with `tectonic`, public WebVoyager states now have rendered teacher-request prompts plus prompt-budget stats, and a one-shot manifest launcher replaced the older standalone sample command path (`3f976bc`).
- `2026-04-21 11:15:08 +0800` - A bootstrap silver-labeler was added for sampled states, and the public WebVoyager example slice now has full recoverability records, SFT splits, and a dry-run controller manifest / launch directory for the first non-toy training pass (`3f976bc`).
- `2026-04-21 11:16:34 +0800` - The paper text and training docs were synced with the bootstrap public-example pipeline, and the draft was recompiled successfully after the protocol update (`3f976bc`).
- `2026-04-21 11:41:14 +0800` - Repository cleanup removed committed toy smoke-test artifacts, the GitHub homepage README was rewritten, and a large public-WebVoyager counterfactual experiment pipeline was added with 167 states, diverse recovery decisions, SFT splits, and a dry-run training manifest (pending current commit).
- `2026-04-21 11:47:31 +0800` - A new root-level `ROADMAP.md` was added to record the current repo snapshot, completed validation, and future optimization directions so both status tracking and forward planning live directly on GitHub (pending current commit).
