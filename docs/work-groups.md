# Work Groups

## Purpose

This document groups the current backlog into batchable work units.

A work group is a small set of related tasks that can be completed in one implementation cycle with:

- one primary goal
- one clear review path
- one shared validation path
- one next-step decision

Use this document together with:

- `AGENTS.md`
- `docs/next-phase-plan.md`
- `docs/todo.md`

## Batch rule

A task belongs in the same work group only when it shares most of the following:

- the same command surface or module area
- the same specialist review agents
- the same validation path
- the same release or documentation impact

If a candidate batch crosses too many unrelated surfaces, split it.

## Review order

Each group should be handled in this order:

1. Product and roadmap agent
2. CLI architect agent
3. Primary specialist agent
4. AI tooling agent if contracts changed
5. QA and release agent

## Current work groups

### WG-01: Google Drive runtime validation

Status:

- blocked by environment credentials or token state

Goal:

- close the real-runtime validation gap for the Drive flow

Batchable tasks:

- verify Drive client-secret env state or local token availability
- run `rfs drive auth`
- run `rfs drive status`
- run `rfs drive search "<query>"`
- record smoke results in `docs/qa-report.md`
- update `docs/next-phase-plan.md` and `docs/todo.md`

Primary agents:

- Product and roadmap agent
- Knowledge integration agent
- AI tooling agent
- QA and release agent

Exit definition:

- real Drive auth is validated in a credentialed environment
- metadata-only search is verified against live data
- remaining Drive gaps are documented or cleared

### WG-02: Research export polish

Status:

- complete

Goal:

- make `rfs research export` easier to hand off into external research workflows

Batchable tasks:

- document NotebookLM-adjacent workflow examples
- review export directory naming and manifest ergonomics
- review whether current default output path is clear enough
- tighten user-facing docs for bundle usage and handoff expectations
- update `docs/research-export-format.md`, `README.md`, and planning docs as needed

Primary agents:

- Product and roadmap agent
- CLI architect agent
- AI tooling agent
- QA and release agent

Exit definition:

- research export usage is documented for real handoff scenarios
- bundle naming and output rules are explicit
- docs and runtime behavior stay aligned

### WG-03: Assistive UX batch A

Status:

- complete

Goal:

- extract the first internal guidance models behind existing `ask` and `shell` behavior

Batchable tasks:

- define `UserIntent`
- define `CommandSuggestion`
- define `GuidanceResponse`
- extract an intent interpreter helper behind `rfs ask`
- extract a suggestion planner helper behind `rfs ask`
- add tests for plain-language command suggestion and short follow-up behavior

Primary agents:

- Product and roadmap agent
- CLI architect agent
- AI tooling agent
- QA and release agent

Exit definition:

- the first assistive UX models exist as internal structures
- `rfs ask` uses extracted helpers instead of growing more inline logic
- tests cover the extracted guidance path

### WG-04: External tool provider design

Status:

- complete

Goal:

- define post-MVP boundaries for local companion tool providers

Batchable tasks:

- define a tool-provider contract
- define a NestClaw adapter boundary
- define a qa_claw adapter boundary
- place all three under post-MVP documentation

Primary agents:

- Product and roadmap agent
- CLI architect agent
- Knowledge integration agent
- AI tooling agent

Exit definition:

- external tool providers have documented boundaries
- no premature runtime integration is introduced

### WG-05: Harbor and game planning

Status:

- complete

Goal:

- keep optional TUI rest-space ideas documented without disturbing the core CLI path

Batchable tasks:

- define an optional `rfs harbor` concept
- define a separate reward or progression model
- define one or two TUI mini-game concepts

Primary agents:

- Product and roadmap agent
- CLI architect agent

Exit definition:

- the concept is documented as optional and post-MVP
- no core product scope is pulled into the game layer

### WG-06: Recovery-first UX copy

Status:

- complete

Goal:

- make direct command empty states and setup blockers easier to recover from

Batchable tasks:

- keep JSON error codes and payload shape stable
- improve text-mode copy for `missing_llm`, `missing_index`, `missing_source`, `not_found`, and `missing_drive_config`
- make `llm status` and `drive status` empty states point to one next command
- add regression tests for human-facing recovery text

Primary agents:

- Product and roadmap agent
- CLI architect agent
- AI tooling agent
- QA and release agent

Exit definition:

- text-mode empty states use short Korean-first recovery copy
- one next step is visible in each key blocked flow
- JSON contract behavior stays unchanged

## Recommended execution order

1. WG-01 when credentials or token state are available

## Current batchable-now list

- none outside blocked tracks

## Current blocked list

- WG-01: Google Drive runtime validation

## Current completed list

- WG-02: Research export polish
- WG-03: Assistive UX batch A
- WG-04: External tool provider design
- WG-05: Harbor and game planning
- WG-06: Recovery-first UX copy
