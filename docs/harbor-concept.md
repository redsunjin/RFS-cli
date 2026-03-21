# Harbor Concept

## Goal

Define a small post-MVP concept for an optional `rfs harbor` rest space.

The purpose of `harbor` is not to replace the core CLI workflow.
Its purpose is to give the user a short, opt-in pause point between tasks without weakening `rfs-cli` as a local-first knowledge and developer agent.

## Core concept

`rfs harbor` is a separate TUI entrypoint for brief rest, reflection, or light optional play.

It should feel adjacent to the main CLI rather than fused into it:

- explicit to enter
- explicit to leave
- safe to ignore completely
- unable to block indexing, search, shell, or agent use

## Product role

`harbor` exists to support the emotional pacing of repeated CLI work, not to become the main product identity.

It may eventually provide:

- a short decompression screen after focused work
- a lightweight celebration or acknowledgement of completed tasks
- one or two optional mini-games with very short sessions

## Command boundary

The first public boundary should remain a separate top-level command:

- `rfs harbor`

The initial concept should avoid spreading harbor behaviors into:

- bare `rfs` startup
- `rfs ask`
- `rfs shell`
- any machine-readable agent command surface

If future subcommands are needed, they should be added only after the single-entry concept is validated.

## Non-goals

This concept does not include:

- replacing the current shell or guidance flow
- making rest or play part of onboarding
- storing progression inside required config or index state
- changing command contracts for `search`, `show`, `dev`, `agent`, or `ask`
- using rewards to gate access to normal CLI functionality
- depending on remote services or online state

## State boundary

Any future harbor state must stay outside the correctness path of the core CLI.

That means:

- harbor state is optional
- harbor state can be reset without affecting indexing or shell behavior
- core commands must keep working when no harbor state exists
- reward or progression data must not alter command output contracts

## Experience principles

- keep sessions short by default
- keep entry and exit friction low
- prefer calming or playful interaction over noisy reward loops
- do not pretend harbor progress is the same as real task completion
- preserve the repository's local-first and low-dependency character

## Acceptance criteria for the first implementation slice

Before any runtime implementation starts, the first harbor slice should satisfy all of these:

1. The command boundary is explicit and separate from the core CLI flow.
2. Core state and harbor state are described as separate concerns.
3. The concept stays optional and post-MVP.
4. The next slices are small enough to validate independently.

## Recommended next slices

1. Design a minimal reward or progression model that stays outside core CLI state.
2. Design one very short TUI mini-game or rest interaction.
3. Decide whether harbor should read any lightweight workspace signals such as completed-session counts without becoming a source of truth.

The first progression slice is documented in `docs/harbor-progression-model.md`.
The first interaction slice is documented in `docs/harbor-first-interaction.md`.
