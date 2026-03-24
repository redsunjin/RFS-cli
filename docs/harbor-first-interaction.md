# Harbor First Interaction

## Goal

Define one very short interaction that can become the first runtime slice for `rfs harbor`.

The interaction should validate the harbor concept without turning `rfs-cli` into a game-heavy product.

## Proposed interaction

The first interaction should be a short calming loop called `Lantern Pause`.

`Lantern Pause` is a brief flow where the user slows down for a few steps, then closes the session explicitly.

## Launch decision

The first runtime version should launch in plain text before any lightweight TUI version is attempted.

Why:

- it validates the pacing and copy first
- it keeps terminal compatibility risk low
- it makes the first implementation easier to ship and reset
- it preserves the option to promote the same loop into TUI later without changing the concept

## Why this interaction fits first

- it matches the "rest space" intent better than a score-chasing game
- it can be completed in under one minute
- it supports the progression model without pressuring the user
- it does not need remote state, complex rendering, or broad command integration

## Session loop

The first loop should stay minimal:

1. Enter `rfs harbor`
2. Choose `Lantern Pause`
3. Show one short settling prompt
4. Guide the user through two or three quiet steps
5. Offer one explicit close action
6. Award a small harbor-local completion acknowledgement

The interaction should never trap the user inside a long loop.

## Example step shapes

The actual writing can change, but the structure should look like this:

- arrive: "잠깐 멈추고 정리할까요?"
- focus: choose one short intention for the break
- settle: wait through a short paced loop or keypress rhythm
- close: confirm completion and return to harbor

The emphasis is on pacing and closure, not challenge.

## Reward behavior

`Lantern Pause` may safely award:

- a small number of `harbor_points`
- one completed session increment
- occasional cosmetic unlock progress

The first guaranteed completion reward should be the cosmetic unlock documented in `docs/harbor-cosmetic-unlocks.md`.

It should not award anything tied to core CLI task volume or task success.

## Non-goals

This first interaction should not include:

- reflex gameplay
- failure states with punishment
- long tutorials
- narrative branching
- integration with `rfs ask` or `rfs shell`
- public machine-readable payloads

## Runtime constraints

- the session should be skippable at any step
- the flow should work without color or advanced terminal features
- the copy should stay short and calming
- the interaction should still make sense if progression storage is unavailable
- the first implementation should not require TUI-specific layout or animation support
- incomplete sessions should restart from the beginning rather than resume automatically

## Acceptance criteria

Before implementation starts, the first interaction should satisfy all of these:

1. A full session can finish in under one minute.
2. The user can cancel without penalty.
3. Completion can award only harbor-local progression.
4. No core command behavior depends on the interaction.

## Recommended next slices

1. Define the minimal cosmetic unlock rule for the first completed sessions.
2. Decide whether the first completion reward should be purely cosmetic or include a small point bonus as well.
3. If a second interaction is ever added, make it slightly more playful while keeping the same low-pressure boundary.

The first reset policy is documented in `docs/harbor-session-reset.md`.
Hidden diagnostic counting is excluded in the first version as documented in `docs/harbor-diagnostic-metrics.md`.
The first cosmetic reward rule is documented in `docs/harbor-cosmetic-unlocks.md`.
