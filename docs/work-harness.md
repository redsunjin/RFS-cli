# Work Harness

`rfs-cli` uses a documentation-first delivery harness built around four stages:

1. Plan
2. Review
3. Execute
4. Verify

The purpose of this harness is to keep each slice small, documented, tested, and safe for both human and agent use.

This delivery loop also sits inside a broader harness structure:

- a control plane that says what the current official work loop is
- a record system that preserves decisions as versioned repository documents
- evaluator and observability signals that prove a slice actually works
- guardrails that prevent branch work from silently replacing official priorities
- a drift-reduction loop that keeps docs, tests, and plans from diverging

## When to use it

Use this harness for any non-trivial change that affects code, behavior, scope, docs, or command contracts.

For tiny edits such as typo fixes or isolated wording changes, the same stages may be collapsed into one short pass as long as no review gate is skipped.

## Harness layers

### 1. Control plane

The control plane decides what the repository is officially optimizing for right now.

Primary artifacts:

- `docs/roadmap.md`
- `docs/todo.md`
- `AGENTS.md`

Rules:

- there should be one official active loop at a time
- branch experiments may extend the repository, but do not replace the official active loop unless the docs explicitly say so
- `docs/todo.md` should name the current official next tasks
- `docs/roadmap.md` should describe the same next slice at the track level

### 2. Record system

The record system preserves durable decisions so a later session can resume without relying on chat history.

Primary artifacts:

- `docs/project-charter.md`
- `docs/product-spec.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/todo.md`
- `docs/harness-worksheet.md` when a slice needs an explicit execution contract

### 3. Evaluator and observability layer

The evaluator layer decides what counts as done, and the observability layer provides enough signal to diagnose failures.

Typical evaluator artifacts:

- `uv run pytest`
- `uv run ruff check .`
- JSON contract tests
- smoke checklists
- QA notes such as `docs/qa-report.md`

Typical observability signals:

- `rfs doctor`
- `rfs doctor --verbose`
- install-flow smoke outcomes
- real-runtime validation notes
- environment-specific waivers when a smoke step cannot run locally

### 4. Guardrails

Guardrails prevent unbounded branch drift.

Examples:

- keep local-first scope ahead of remote expansion
- do not widen machine-readable contracts without AI tooling review
- do not let branch-only idea work silently replace the documented official loop
- do not mark a slice complete when docs, tests, and implementation disagree

### 5. Drift and hygiene

The harness should make drift visible and reduce it in small increments.

Current hygiene rules:

- keep roadmap and TODO next-slice notes aligned
- promote repeated review rules from prose into tests or scripts when possible
- prefer small cleanup slices over large deferred reconciliation work

## Stage 1: Plan

Goal:
Select one bounded slice and confirm that it still belongs to the current phase.

Primary owner:
Product and roadmap agent

Supporting roles:
- CLI architect agent
- relevant specialist agent for the domain

Inputs:
- `docs/project-charter.md`
- `docs/product-spec.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/todo.md`
- attached notes or transient materials that contain durable requirements

Required checks:
- the change has a clear user-facing or system-facing outcome
- the slice is small enough to finish with docs, code, and tests in one cycle
- the change does not pull later-phase scope into the current slice

Outputs:
- one selected slice
- a short statement of intent
- the documents likely to change
- the specialist roles needed for the slice
- a worksheet reference when the slice is large enough to need a durable execution contract

## Stage 2: Review

Goal:
Confirm the shape of the change before implementation expands it.

Primary owner:
CLI architect agent

Supporting roles:
- Product and roadmap agent
- AI tooling agent when command behavior or payloads may change
- specialist domain agent when source handling, retrieval, or integrations are involved

Required checks:
- command naming stays coherent
- module boundaries stay coherent
- output contracts remain stable or have an explicit review path
- docs impact is understood before code changes begin

Outputs:
- design confirmation or a narrowed scope
- contract notes when JSON or error payloads are touched
- explicit review gates for the slice
- confirmation that the slice still belongs to the official active loop, or an explicit note that it is branch-only exploratory work

## Stage 3: Execute

Goal:
Implement the selected slice without expanding scope.

Primary owner:
Primary implementation agent

Supporting roles:
- relevant specialist implementation agent

Required checks:
- keep the CLI usable during the change
- preserve documented command names
- update docs when behavior or scope changes
- add or update tests for changed behavior

Outputs:
- code changes
- doc updates
- tests for the new or changed behavior

## Stage 4: Verify

Goal:
Prove that the slice is complete, aligned, and ready to hand off.

Primary owner:
QA and release agent

Supporting roles:
- AI tooling agent when command contracts changed
- Product and roadmap agent when scope or milestone status changed

Required checks:
- docs and implementation agree
- tests exist for the changed behavior
- validation passes for the slice
- command contract changes have AI tooling review
- the slice did not add later-phase scope

Typical validation:
- `uv run pytest`
- `uv run ruff check .`
- focused contract checks for JSON payloads and errors
- manual smoke checks when a flow cannot be fully automated

Required handoff artifacts:
- updated docs if behavior or scope changed
- tests for the new or changed behavior
- a brief validation result
- a clear next slice recommendation
- roadmap/TODO sync when a track-level “next slice” changed

## Review gates

Do not mark a slice complete if any of the following are true:

- docs and implementation disagree
- tests are missing for changed behavior
- a command contract changed without AI tooling review
- the slice added scope that belongs to a later phase

## Document update order

When a feature changes scope or behavior, update documents in this order:

1. `docs/project-charter.md`
2. `docs/product-spec.md`
3. `docs/architecture.md`
4. `docs/roadmap.md`
5. `docs/todo.md`

## Roadmap and TODO sync rule

When `docs/roadmap.md` names a track-level next slice, `docs/todo.md` should either:

- contain a matching open checklist item, or
- explicitly mark that track as exploratory and outside the official active loop

Do not leave a roadmap “next slice” without a corresponding TODO interpretation.

## Execution worksheet rule

For larger slices, branch-only tracks, or work that changes more than one workstream, create a worksheet from `docs/harness-worksheet.md`.

A worksheet should capture:

- which track the slice belongs to
- whether it is official-loop work or branch-only work
- what documents are the source of truth
- what validation and runtime signals will be used
- what drift risks or cleanup follow-ups are expected

Small self-contained slices may skip a separate worksheet if the same information is obvious from the updated docs and handoff summary.

## Role mapping

- Product and roadmap agent: owns scope, priorities, and milestone alignment
- CLI architect agent: owns command shape, module boundaries, and design coherence
- Knowledge integration agent: reviews adapters, extraction behavior, and source-specific edge cases
- Search and retrieval agent: reviews ranking, filters, snippets, and recall behavior
- AI tooling agent: reviews machine-readable contracts, error models, and agent safety
- QA and release agent: validates tests, regressions, and release readiness

## Default operating pattern

For a normal slice, the repository should move through this sequence:

1. Plan the slice from `docs/todo.md` or the active roadmap phase
2. Review command shape and contract impact
3. Execute code, docs, and tests in one bounded pass
4. Verify with validation and a short handoff summary

This document formalizes the workflow that is already reflected in `AGENTS.md` and should be treated as the default delivery harness for the repository.
