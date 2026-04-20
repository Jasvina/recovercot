# RecoverCoT Experiment Plan

This note keeps the initial repository focused while preserving the shortest path from the current draft to an empirical EMNLP submission.

## MVP

- Build an offline counterfactual recoverability dataset from WebVoyager/OpenWebVoyager-style trajectories.
- Train a 7B/8B instruction model with LoRA to emit recoverability JSON.
- Evaluate offline decision accuracy, rollback target accuracy, and pairwise recovery ranking.
- Run a small online validation on WebVoyager and Mind2Web-Live.

## Labels

For each sampled state, compare:

- continue from the current state;
- branch with an alternative next action;
- rollback to the most recent checkpoint;
- rollback to an earlier semantic checkpoint;
- restart or terminate.

The selected label is the candidate with the best success/cost tradeoff under a fixed rollout budget.

## Main Baselines

- Greedy web agent.
- WebCoT-style reasoning prompt/SFT.
- WebRollback-style explicit rollback.
- Scalar process reward reranking.

## Key Metrics

- Task success rate.
- First-error recovery rate.
- Rollback precision.
- Unnecessary rollback rate.
- Rollback target accuracy.
- Average steps and token cost.
