# Next Phase Plan

## Date

2026-03-14

## Current active stage

Stage 4: Post-MVP expansion

## Planning intent

This plan starts from the current state of `rfs-cli` as a nearly signed-off MVP and defines the next execution order.
The goal is to keep the signed-off MVP usable as a dependable personal CLI agent, then expand only after the release baseline is clear.

## Current baseline

- local and Obsidian indexing/search are implemented
- developer utilities are implemented
- machine-readable JSON contracts are implemented
- required LLM onboarding is implemented
- interactive shell mode is implemented
- bare `rfs` startup now opens onboarding or shell automatically in interactive terminals
- local real-data smoke is complete
- real Obsidian smoke remains environment-blocked

## Execution order

### Stage 1: MVP sign-off closeout

Goal:

Close the last environment-specific MVP question and lock the release baseline.

Status:

Completed in the current environment.

Notes:

- LM Studio runtime validation for `rfs llm status`, `rfs ask`, and `rfs shell` is complete
- LM Studio/Qwen output sanitation was added after runtime validation exposed reasoning-tag leakage
- the Obsidian real-data smoke item is waived for this environment because no real vault path is available

### Stage 2: Agent guidance hardening

Goal:

Make the CLI agent more useful at the moment a user does not know the exact command.

Tasks:

- define the persona and response-style contract in a stable document
- make `rfs ask` aware of configured sources and index state
- add one-short-follow-up behavior for ambiguous asks
- improve shell guidance so the agent recommends executable commands before broad explanation

Current slice status:

- persona and response-style contract: complete
- source-aware and index-aware `rfs ask`: complete
- short follow-up behavior: complete
- richer shell guidance grounding: complete

Status:

Completed.

Exit definition:

- persona contract is documented
- guidance answers are grounded in real state
- ambiguous asks trigger a short follow-up instead of generic output

### Stage 3: Release readiness baseline

Goal:

Prepare the current CLI agent for dependable ongoing personal use.

Tasks:

- define installation flow clearly for local and tool-style usage
- add release checklist and versioning policy
- add basic logging and diagnostics switches
- run an end-to-end smoke pass on the final baseline

Current slice status:

- installation flow baseline: complete
- release checklist baseline: complete
- versioning policy: complete
- diagnostics and logging basics: complete
- end-to-end install-flow smoke: complete
- user-facing agent profile: complete

Status:

Completed in the current environment.

Exit definition:

- install/use/recover flows are documented
- release checklist exists
- operational diagnostics are sufficient for local debugging

### Stage 4: Post-MVP expansion

Goal:

Expand only after the core agent baseline is stable.

Candidate tracks:

- Google Drive integration
- NotebookLM-adjacent export workflows
- external tool provider contracts for NestClaw and qa_claw
- optional harbor/rest TUI gamification track

Current slice status:

- Drive source config model: complete
- Drive auth and cache boundary: complete
- Drive metadata retrieval shape and response contract: complete

## Recommended next three tasks

1. Implement the Google Drive auth flow.
2. Implement Google Drive file metadata retrieval.
3. Implement the Google Drive cache strategy.
