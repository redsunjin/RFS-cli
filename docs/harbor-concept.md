# Harbor Concept

## Date

2026-03-17

## Status

Post-MVP optional concept only. No runtime implementation is planned in the current release line.

## Purpose

`rfs harbor` is an optional TUI rest space for short pauses between core CLI tasks.
It should reinforce the Ready For Sea identity without interrupting indexing, search, diagnostics, or agent workflows.

## Command boundary

The harbor should stay behind one separate top-level boundary:

- `rfs harbor`

Possible subcommands later:

- `rfs harbor status`
- `rfs harbor rest`
- `rfs harbor play fishing`
- `rfs harbor play signal`
- `rfs harbor logbook`

## Product rules

- fully optional
- no effect on required onboarding, indexing, search, or release readiness
- no coupling to command contracts used by automation
- no hidden rewards that make the core CLI worse when unused
- no write access to core config or index state

## Separate state model

If implemented later, harbor state should be stored separately from required CLI state.

Suggested file:

- `.rfs/harbor.json`

Suggested fields:

- `schema_version`
- `visited_at`
- `voyage_points`
- `map_fragments`
- `logbook_entries`
- `unlocked_games`

This state should remain safe to delete without damaging normal CLI workflows.

## Reward model

Rewards should stay light and cosmetic.

Suggested rules:

- indexing or successful research export can award small voyage progress
- diagnostics or cleanup tasks can unlock logbook notes or badges
- no reward should be required to access a real CLI feature

## First mini-game concepts

### Fishing

- 30 to 60 second input-timing mini-game
- low cognitive load
- suitable for a short reset between tasks

### Signal

- short decode or pattern-matching mini-game
- text-first and terminal-friendly
- aligned with the CLI theme of interpretation and guidance

## Exit criteria for future implementation

- the harbor is clearly separated from core CLI state
- all harbor commands are optional and safe to ignore
- the TUI works in a normal terminal without breaking non-interactive usage
- core command contracts remain unchanged
