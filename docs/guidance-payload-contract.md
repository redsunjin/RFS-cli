# Guidance Payload Contract Review

## Goal

Define the review gate that must be passed before `rfs-cli` exposes any broader machine-readable guidance payload.

## Current rule

Human-facing guidance may continue to evolve in text mode.
Machine-readable guidance must not expand implicitly through `ask`, `shell`, or any future agent-facing command.

## Current public JSON contract

Today, `rfs ask --format json` is the only implemented guidance-adjacent JSON surface.
Its public `data` shape stays limited to:

- `question`
- `provider`
- `model`
- `answer`
- `follow_up_required`
- `follow_up_question`

Current constraints:

- no `recommended_command`
- no `mode`
- no `summary`
- no `alternatives`
- no shell-memory snapshot
- no doctor-diagnostics snapshot
- no internal intent or suggestion payload

## Why the contract stays narrow

- text guidance is still being iterated quickly
- internal suggestion models are still experimental
- shell-memory and doctor-visible grounding are implementation details, not yet public schema
- AI callers need stable fields more than they need rich experimental metadata

## Required review before expansion

Any new machine-readable guidance field must answer all of these questions:

1. Is the field stable across `ask` and any future guidance entrypoint?
2. Is the field derived only from supported commands and observable local state?
3. Can the field be versioned without breaking existing automation?
4. Does the field avoid leaking raw internal prompts, shell history, or unstable reasoning details?
5. Does the field distinguish read-only from state-changing recommendations clearly enough for automation?
6. Do contract tests fail if the field is removed, renamed, or reshaped accidentally?

## Required delivery artifacts for expansion

Do not widen the machine-readable guidance payload unless the same slice includes:

- updated product and architecture docs
- an explicit schema example
- contract tests for the new payload shape
- AI tooling review sign-off recorded in roadmap and TODO updates

## Safe near-term path

The safe next step is not to expose the full internal guidance model.
It is to keep the current `ask` JSON contract frozen until one reviewed schema can cover:

- deterministic follow-up questions
- grounded recommended commands
- read-only versus state-changing intent
- bounded explanation text

## Non-goals for this review

- no new JSON fields in the current slice
- no `shell --format json`
- no streaming guidance protocol
- no provider-specific guidance schema
