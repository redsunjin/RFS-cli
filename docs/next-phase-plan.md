# Next Phase Plan

## Date

2026-03-17

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
- Drive auth flow and local token persistence: complete
- Drive file metadata retrieval: complete
- Drive local metadata cache strategy: complete
- Live metadata-only `drive search`: complete
- Drive adapter integration tests: complete
- Real Google Drive smoke: blocked in the current environment because no Drive client-secret env vars or token file are available
- Cache expiry and invalidation review: complete through command-level cache-hit, expiry, and page-size invalidation tests
- Research export bundle format: complete
- First `rfs research export` command: complete
- NotebookLM-adjacent workflow examples: complete
- Research export bundle naming review: complete
- Internal `UserIntent`, `CommandSuggestion`, and `GuidanceResponse` models: complete
- First extracted guidance planner behind `rfs ask`: complete
- Shared external tool-provider contract: complete
- NestClaw adapter boundary: complete
- qa_claw adapter boundary: complete
- Intent categories now distinguish add-source, search, inspect, and diagnose more explicitly
- Guidance suggestions now use path hints, source-kind hints, index validity, and doctor-visible state more deeply
- Startup and shell help now lead with a smaller "start here" section
- Deterministic guidance now marks read-only versus state-changing recommendations
- Guidance contract review is now documented before any broader machine-readable payload expansion
- Startup and shell help now reuse internal help-block models instead of ad-hoc local strings
- Harbor and game planning is now documented as a completed optional concept track
- The next unblocked follow-on batch is recovery-first direct-command copy for empty states and setup blockers
- Recovery-first direct-command copy is now implemented for key blocked flows while JSON contracts remain stable
- The current `ask` contract is now validated against a human-in-the-loop automation scenario
- Guidance now supports deterministic source-listing and recent internal-command recall

## Recommended next three tasks

1. Run a real Google Drive smoke pass when client secrets or token state are available.
2. Record the real Google Drive smoke result in QA docs once credentials are available.
3. Keep any future guidance-payload expansion behind a dedicated contract review note.

## Current work-group execution order

Use `docs/work-groups.md` as the batch-planning layer above individual TODO items.

Current order:

1. `WG-01` Google Drive runtime validation when credentials or token state are available
