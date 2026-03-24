# Harbor Cosmetic Unlock Rule

## Goal

Define the first cosmetic unlock rule for completed `Lantern Pause` sessions.

## First-version rule

The first completed `Lantern Pause` session should unlock one small cosmetic reward immediately.

That first unlock should be:

- guaranteed on the first completed session
- purely cosmetic in effect
- visible inside `rfs harbor`
- safe to ignore without changing normal CLI use

## Proposed first unlock

The initial cosmetic unlock should be a simple harbor theme marker called `soft_glow`.

This can later appear as:

- a small label in harbor status
- a changed lantern name or caption
- an alternate decorative line in harbor copy

The exact presentation can evolve later.
The important part of the rule is that the unlock is cosmetic only and tied to completion, not performance.

## Unlock rule

For the first version:

- first completed session unlocks `soft_glow`
- incomplete sessions unlock nothing
- repeated completions do not re-award the same cosmetic
- lack of cosmetic state must not block harbor entry

This makes the first reward easy to explain:
finish once, unlock one small cosmetic.

## Why this fits first

- it gives a clear sense of closure without adding pressure
- it avoids gameplay power or utility advantages
- it works in plain text before any TUI styling exists
- it keeps progression lightweight and optional

## Non-goals

This rule does not include:

- power-ups
- command shortcuts
- changes to search, shell, or agent behavior
- random loot or chance-based rewards
- reward scaling based on speed or skill

## Acceptance criteria

Before implementation starts, the first cosmetic rule should satisfy all of these:

1. The first completed session always unlocks the same cosmetic reward.
2. Incomplete sessions unlock nothing.
3. The cosmetic does not affect core CLI correctness or capability.
4. The rule is understandable in one short sentence.

## Recommended next slices

1. Decide whether the first completion should also grant a small point bonus or stay cosmetic-only.
2. Define how harbor status should show unlocked cosmetics in plain text.
3. If later unlocks are added, keep them sparse and cosmetic-first.
