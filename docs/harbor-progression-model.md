# Harbor Progression Model

## Goal

Define the smallest optional reward or progression model for `rfs harbor`.

The purpose of this model is to add a light sense of continuity inside `harbor` without changing the correctness, onboarding, or command behavior of the core CLI.

## Design intent

The first progression model should be:

- optional
- local-only
- easy to reset
- small enough to explain in one screen
- unable to affect indexing, search, shell, or agent contracts

## What progression should represent

Progression should reflect optional harbor participation, not authoritative productivity.

The first model may acknowledge simple events such as:

- entering `rfs harbor`
- completing a short harbor session
- finishing an optional rest interaction or mini-game
- returning on multiple distinct days

It should not claim to measure real work quality, project completion, or personal performance.

## First model shape

The initial model should stay minimal:

- `harbor_level`: a small integer for broad progression
- `harbor_points`: a lightweight score for optional accumulation
- `session_count`: total completed harbor sessions
- `streak_days`: count of recent distinct days with harbor use
- `last_session_at`: timestamp of the last completed harbor session
- `unlocked_cosmetics` or similar optional cosmetic markers

This is a product model, not a fixed runtime schema.
Implementation details can change later as long as the same boundaries hold.

## Safe reward sources

The first implementation should reward only harbor-local actions such as:

- finishing a short rest loop
- completing an opt-in mini-game
- returning after a break
- acknowledging a completed harbor session explicitly

Avoid rewards based directly on:

- number of indexed files
- number of search results
- number of shell commands run
- success or failure of core CLI commands
- external services or remote activity

## State boundary

Any future progression state must stay outside the core workspace state required for normal CLI operation.

That means:

- harbor progression can be absent without degrading the rest of `rfs-cli`
- harbor progression can be deleted or reset safely
- core commands must not read progression state to decide correctness or permission
- agent-facing JSON payloads must not depend on harbor progression

## User experience rules

- rewards must stay low-pressure
- progression must be understandable without a long tutorial
- cosmetics are safer than power-ups
- skipped sessions must not punish the user harshly
- the system should celebrate lightly, not manipulate aggressively

## Non-goals

This model does not include:

- gating core features behind level or points
- competitive leaderboards
- remote sync
- daily chores required for normal CLI use
- hidden bonuses tied to core command usage
- progression-based changes to `ask` or `shell` behavior

## Recommended persistence shape

If implemented, progression should live in an optional harbor-specific file rather than in existing required state such as config, index data, or shell memory.

The persistence should be:

- local
- human-inspectable if practical
- versionable if it becomes durable
- isolated enough that corruption does not impact core CLI flows

## Acceptance criteria for the first implementation slice

Before runtime work starts, the progression model should satisfy all of these:

1. Core CLI correctness does not depend on progression state.
2. Reward sources are harbor-local and opt-in.
3. Resetting progression is safe and unsurprising.
4. The model can be implemented without changing public command contracts outside `rfs harbor`.

## Recommended next slices

1. Design one short harbor interaction that can award points safely.
2. Decide whether progression should expose only cosmetic unlocks in the first runtime version.
3. Define a reset and recovery story for corrupted harbor state.

The first interaction candidate is documented in `docs/harbor-first-interaction.md`.
Incomplete sessions should restart cleanly without rewards as documented in `docs/harbor-session-reset.md`.
The first cosmetic reward rule is documented in `docs/harbor-cosmetic-unlocks.md`.
