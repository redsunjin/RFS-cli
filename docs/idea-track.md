# Idea Track

## Date

2026-03-15

## Branch intent

This branch is the experimental product-shaping track for `rfs-cli`.

The goal is not to replace the stable CLI baseline on `main`, but to explore how `rfs` can become easier for non-developer users through AI-assisted help, command suggestion, and modular guidance behavior.

## Direction statement

`rfs-cli` should become a local-first knowledge and workspace assistant that lets a user describe a task in plain language, then receive a safe and concrete next step instead of a generic help dump.

Related reference:

- `docs/easy-cli-principles.md`

## Constraints

- keep the documented top-level command surface stable unless a change is clearly justified
- prefer internal module seams over new top-level commands during experimentation
- keep human guidance grounded in current local state, configured sources, and implemented commands
- do not let the AI layer drift into general-purpose chat
- require AI tooling review before any machine-readable guidance payload becomes public contract

## First experimental modules

### 1. Intent interpreter

Purpose:

Turn plain-language requests into a small, explicit task model.

Initial responsibilities:

- detect the user's likely goal such as setup, add-source, search, inspect, or diagnose
- extract obvious entities such as source name, path, file type, or query text
- identify the single most important missing detail
- return one short follow-up question when a request is not actionable yet

### 2. Suggestion planner

Purpose:

Map the interpreted task plus runtime state to the best supported command path.

Initial responsibilities:

- use current config, index, and shell state as grounding inputs
- rank candidate commands and decide whether to suggest, defer, or redirect
- distinguish read-only help from state-changing actions
- detect when onboarding, indexing, or doctor-style recovery should be suggested first

### 3. Guidance renderer

Purpose:

Explain the next step in plain language without hiding the real command.

Initial responsibilities:

- lead with one recommended command
- explain why that command fits the user's task
- provide one fallback or alternative when needed
- keep wording short and Korean-first by default

## Entry points for the first slice

- bare `rfs` startup
- `rfs ask`
- natural-language requests inside `rfs shell`
- selected error and empty-state messages

## Merge criteria back to stable line

- docs and runtime behavior agree
- the guidance stays bounded to implemented commands
- changed behavior has automated coverage
- any new JSON or machine-readable payload has explicit schema review

## Current status

- machine-readable guidance contract review is now documented
- startup and shell help now share reusable internal help-block models
- the public machine-readable guidance contract remains limited to `ask --format json`
- key direct-command empty states now use recovery-first Korean copy with one next step
- the current contract is now validated against a human-in-the-loop automation use case
- guidance can now list connected sources and recall the most recent internal command deterministically

## Recommended next slice

1. keep new guidance fields behind explicit contract review instead of growing ad hoc payloads
2. continue improving human-facing help text without exposing startup or shell help as public API
3. reopen contract expansion only if unattended execution becomes an approved requirement
