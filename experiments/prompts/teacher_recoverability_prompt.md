# Teacher Prompt: Recoverability Labeling

You are labeling one intermediate state from a long-horizon web-agent task.
Your job is to decide whether the current state is still recoverable and what the best recovery decision is under a limited remaining budget.

## Inputs

- Task instruction
- Current observation summary
- Recent trajectory history
- Candidate rollback checkpoints
- Candidate next-step options
- Remaining step budget

## Label Definitions

### Recoverability

- `recoverable`: a realistic path to success exists with low or moderate cost.
- `weakly_recoverable`: a path to success may still exist, but it is fragile, costly, or uncertain.
- `irrecoverable`: success is no longer realistic under the remaining budget.

### Decision

- `continue`: stay on the current trajectory and keep going.
- `branch`: try a different next action without restoring an earlier checkpoint.
- `rollback`: restore a previous checkpoint and continue from there.
- `restart`: abandon the current trajectory and start over, or terminate if restart is unavailable.

## Output Requirements

Return valid JSON with exactly these top-level keys:

- `recoverability`
- `decision`
- `rollback_target`
- `teacher_rationale`
- `candidate_scores`

Rules:
- `rollback_target` must be `null` unless `decision` is `rollback`.
- `candidate_scores` must contain numeric scores for all candidates that were shown.
- `teacher_rationale` must be concise and grounded in the visible state.
- Do not mention hidden knowledge or unsupported assumptions.

## Output Format

```json
{
  "recoverability": "weakly_recoverable",
  "decision": "rollback",
  "rollback_target": "checkpoint_3",
  "teacher_rationale": "The agent chose a wrong category branch, and later filters depend on that branch.",
  "candidate_scores": {
    "continue": 0.21,
    "branch": 0.46,
    "rollback:checkpoint_2": 0.52,
    "rollback:checkpoint_3": 0.81,
    "restart": 0.18
  }
}
```
