# RecoverCoT Paper

Clean standalone paper repository for:

> RecoverCoT: Counterfactual Recoverability Distillation for Robust Web Agents

The repository is intentionally small: paper source, bibliography, and minimal build metadata only.

## Layout

- `paper/main.tex` — ACL/EMNLP-style draft.
- `paper/references.bib` — bibliography for the current related work.
- `docs_experiment_plan.md` — concrete MVP experiment plan.
- `experiments/` — prompt/schema/example/validator scaffold for recoverability labels.
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
make eval-sample
make build-sample-sft
make paper
```
