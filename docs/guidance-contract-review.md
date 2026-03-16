# Guidance Contract Review

## Date

2026-03-15

## Purpose

Freeze which parts of assistive guidance are public contract and which parts remain internal implementation detail.

## Decision summary

- The machine-readable guidance contract is public only for `rfs ask --format json`.
- Startup help and shell help remain human-facing text surfaces, not machine-readable contract.
- Internal planning models such as `UserIntent`, `CommandSuggestion`, `GuidanceResponse`, and help-block models remain implementation detail.
- Any new machine-readable guidance field requires explicit AI-tooling review before release.

## Public contract now

The stable public guidance payload is the existing `CommandPayload` for `ask` with these fields under `data`:

- `answer`
- `follow_up_required`
- `follow_up_question`
- `action_type`

These fields may be consumed by downstream automation and should be treated as versioned behavior.

## Internal-only guidance surfaces

The following are intentionally internal and may change faster:

- startup "Start here" block structure
- shell `/help` block structure
- internal intent-classification labels
- deterministic suggestion ranking details
- internal help block models used to render human-facing help

## Review rule

Before any new machine-readable guidance shape is exposed:

1. update product and architecture documents
2. document why the field belongs in public contract instead of internal guidance
3. add contract tests
4. record the review outcome in planning docs

## Current conclusion

Keep guidance payload expansion conservative.
Prefer evolving human-facing help text and internal guidance models first, and expose new machine-readable fields only when a clear automation use case exists.

## Validated automation boundary

The current contract has now been validated against a human-in-the-loop automation scenario.
That review confirms that the existing `ask` payload is sufficient for showing one next step, pausing on follow-up questions, and separating read-only from state-changing guidance without exposing more internal planning detail.
