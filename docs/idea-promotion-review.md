# Idea Promotion Review

## Goal

Compare the current official loop with the completed idea-branch experiments and identify which finished idea work is most suitable for promotion into the official loop.

This document is a review artifact only.
It does not change the official active loop by itself.

## Current official loop level

The current official loop is still:

1. run a real Google Drive smoke pass
2. design a NestClaw adapter boundary
3. design a `qa_claw` adapter boundary

This means the official loop is currently:

- post-MVP
- integration-oriented
- validation-oriented
- low on new UX scope

The official loop is not currently focused on:

- harbor
- personal agent knowledge promotion
- broader assistive UX expansion

## Completed idea work with real implementation

### 1. Assistive UX

Implemented and documented:

- internal guidance modules
- deterministic follow-up path
- progressive help for bare `rfs`, `--help`, `ask`, and `shell`
- Korean recovery copy
- read-only versus state-changing labels
- `rfs doctor --verbose` grounding
- guidance contract review

Status:

- implementation exists
- tests exist
- docs exist
- public JSON expansion intentionally deferred

### 2. Personal agent knowledge

Implemented and documented:

- agent-skill-knowledge model
- note templates for `Agents/`, `Skills/`, and `Sources/`
- note-backed registry surface
- `rfs agent list-notes --kind role|skill`
- `rfs agent show-note <id>`
- exact list/show JSON examples

Status:

- implementation exists
- tests exist
- docs exist
- scope is read-only and safe

### 3. Harness strengthening

Implemented and documented:

- formal work harness
- worksheet template
- roadmap/TODO control-plane rules
- harness sync checker

Status:

- implementation exists
- docs exist
- machine check exists
- already functions as process infrastructure

## Mostly-designed but not promoted candidates

### Harbor / gamification

Completed mostly as design decisions:

- harbor concept
- progression model
- Lantern Pause interaction
- plain-text first decision
- reset policy
- cosmetic unlock

Not yet present:

- runtime command implementation
- user validation
- test-backed product behavior

Status:

- strong design exploration
- weak runtime maturity

## Promotion comparison

| Candidate | Runtime maturity | Test coverage | Contract risk | Product fit | Promotion readiness |
|-----------|------------------|---------------|---------------|-------------|---------------------|
| Assistive UX | high | high | medium | high | strong |
| Personal agent knowledge | high | high | low | high | strongest |
| Harness strengthening | high | medium | low | medium | strong |
| Harbor | low | low | low | medium | weak |

## Why personal agent knowledge is the strongest candidate

Reasons:

- it already has implemented commands, not only internal helpers
- it is local-first and read-only
- it does not destabilize machine contracts broadly
- it aligns with the long-term direction of `rfs-cli` as a personal agent environment
- it can be promoted without forcing unfinished JSON or execution automation decisions

## Why assistive UX is the second candidate

Reasons:

- the implementation is real and useful
- the UX quality gains are visible
- but it still carries more contract caution than the registry track
- the public JSON guidance surface is intentionally frozen, so promotion should be selective rather than broad

## Why harbor should stay experimental

Reasons:

- it is mostly design-complete, not runtime-complete
- it does not help close the current official integration loop
- it is easier to keep as an isolated branch track until real runtime validation exists

## Recommended promotion order

1. personal agent knowledge
2. selected assistive UX behaviors
3. harness/process improvements that support both official and branch work
4. keep harbor experimental until runtime exists

## Safe promotion rule

If one idea candidate is promoted, do it by:

1. naming it explicitly in both `docs/roadmap.md` and `docs/todo.md`
2. keeping the official loop small
3. promoting one candidate at a time
4. not promoting harbor and broad assistive UX together in the same slice

## Current recommendation

If the official loop is intentionally paused for idea promotion, the first promotion candidate should be:

- personal agent knowledge, specifically the read-only note registry path

The first concrete promotion slice would be:

- decide that the registry stays indexing-backed with no separate store

That slice is:

- already prepared by the current docs
- narrow
- safe
- aligned with implemented behavior
