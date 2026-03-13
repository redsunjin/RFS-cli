# Next Phase Plan

## Date

2026-03-13

## Planning intent

This plan starts from the current state of `rfs-cli` as a nearly signed-off MVP and defines the next execution order.
The goal is to finish MVP sign-off cleanly, then improve the CLI agent's guidance quality before expanding into new integrations.

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

Tasks:

- run one real Obsidian vault smoke pass if a vault path becomes available
- if no vault is available, document and approve an environment-specific waiver
- validate `rfs llm status`, `rfs ask`, and `rfs shell` against a real LM Studio or Ollama runtime
- keep regression checks green during that validation work

Exit definition:

- MVP sign-off decision is explicit
- runtime validation notes are captured
- no blocking defects remain open

### Stage 2: Agent guidance hardening

Goal:

Make the CLI agent more useful at the moment a user does not know the exact command.

Tasks:

- define the persona and response-style contract in a stable document
- make `rfs ask` aware of configured sources and index state
- add one-short-follow-up behavior for ambiguous asks
- improve shell guidance so the agent recommends executable commands before broad explanation

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

## Recommended next three tasks

1. Validate `rfs ask` and `rfs shell` against the real LM Studio runtime already available in the environment.
2. Decide and document the Obsidian real-data smoke requirement or waiver for MVP sign-off.
3. Draft the agent persona and response-style contract that governs `rfs ask` and `rfs shell`.
