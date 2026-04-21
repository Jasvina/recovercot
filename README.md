# RecoverCoT Paper

Clean standalone paper repository for:

> RecoverCoT: Counterfactual Recoverability Distillation for Robust Web Agents

The repository is intentionally small: paper source, bibliography, and minimal build metadata only.

## Layout

- `STATUS.md` — the primary progress surface to monitor current stage and next actions.
- `paper/main.tex` — ACL/EMNLP-style draft.
- `paper/references.bib` — bibliography for the current related work.
- `experiments/` — prompt/schema/example/validator scaffold for recoverability labels.
- `training/` — config and run-manifest scaffold for controller fine-tuning.
- `paper/README.md` — local build notes.

## Repository Status

- Remote: `git@github.com:Jasvina/recovercot.git`
- Branch: `main`
- Scope: paper-first repository only; no legacy project files carried over
- CI: `.github/workflows/validate.yml` runs the sample data/label pipeline on push and pull request

## Current Draft Stage

- The core paper framing, method, metrics, and experiment protocol are written.
- Numerical results are intentionally not fabricated and still need real experiments.
- The repository is ready for iterative paper writing plus future experiment scripts/data manifests.

## Push / Pull

```bash
git pull --ff-only origin main
git push -u origin main
```

## Useful Local Commands

```bash
make validate-sample
make sample-pipeline
make build-sample-records
make eval-sample
make build-sample-sft
make benchmark-samples
make build-sample-manifest
make paper
```
