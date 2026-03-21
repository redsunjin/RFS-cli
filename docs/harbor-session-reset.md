# Harbor Session Reset Policy

## Goal

Define the first persistence and reset behavior for incomplete `Lantern Pause` sessions.

The goal is to keep the first runtime version simple, predictable, and low-risk.

## First-version rule

For the first runtime version, incomplete harbor sessions should not be resumable.

If a user leaves `Lantern Pause` early, the system should:

- treat the session as incomplete
- award no points
- increment no completion count
- start from the beginning the next time

This keeps the first implementation easy to explain and easy to recover from.

## What counts as incomplete

A session is incomplete if the user:

- cancels intentionally
- exits `rfs harbor`
- closes the terminal
- loses the process before the close step finishes

Only an explicit successful close should count as a completed session.

## Persistence rule

The first version should avoid durable step-by-step session persistence.

That means:

- no saved mid-session checkpoint
- no automatic resume
- no partial reward carry-over
- no dependence on incomplete-session data for later sessions

If a temporary marker is ever used for crash cleanup, it should be safe to delete automatically and should not become a user-facing source of truth.

## Reset rule

Reset behavior should be simple:

- next launch starts a fresh `Lantern Pause`
- stale incomplete-session markers, if they exist, may be cleared automatically
- progression state stays unchanged after an incomplete session

The user should not need to run a repair command for normal early exits.

## Why this is the right first step

- it keeps the plain-text first launch small
- it avoids tricky resume logic before the interaction is validated
- it prevents confusing "half-complete" reward states
- it preserves the option to add resume later only if the interaction proves worthwhile

## Non-goals

This policy does not include:

- resumable checkpoints
- partial rewards
- abandonment penalties
- recovery prompts that block normal harbor entry
- links to core CLI correctness or diagnostics

## Acceptance criteria

Before implementation starts, the first reset policy should satisfy all of these:

1. Incomplete sessions never award completion-based progression.
2. A fresh launch always works even after a crash or forced exit.
3. The user does not need to understand internal state recovery.
4. The policy does not change behavior outside `rfs harbor`.

## Recommended next slices

1. Define the minimal cosmetic unlock rule for the first completed sessions.
2. Decide whether the first completion reward should be purely cosmetic or include a small point bonus as well.
3. If runtime implementation begins, keep the first persistence path optional and harbor-specific.

Hidden diagnostic counting is excluded in the first version as documented in `docs/harbor-diagnostic-metrics.md`.
