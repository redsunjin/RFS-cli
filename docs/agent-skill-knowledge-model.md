# Agent Skill Knowledge Model

## Goal

Define how `rfs-cli` should treat agent roles, reusable skills, and personal knowledge storage as one connected system.

The purpose of this model is to let the project grow into a practical personal agent environment rather than a loose collection of CLI commands.

## Core idea

The model has three layers:

1. Agent roles
2. Skills
3. Knowledge notes

Each layer serves a different purpose:

- agent roles decide who should think about a task
- skills define how a repeatable task should be carried out
- knowledge notes preserve context, examples, references, and decisions

## Layer 1: Agent roles

Agent roles are stable operating perspectives such as:

- product and roadmap
- CLI architecture
- knowledge integration
- search and retrieval
- AI tooling
- QA and release

Roles should remain small in number and stable over time.
They are planning and review lenses, not a collection of every possible prompt.

`AGENTS.md` remains the primary definition for repository-level roles.

## Layer 2: Skills

Skills are reusable execution assets.

A skill may include:

- a prompt or instruction pattern
- a checklist
- a command recipe
- a review rubric
- a short workflow for a recurring task

Skills should be:

- narrower than agent roles
- reusable across multiple tasks
- stored as durable project assets rather than hidden in one-off chats

Examples:

- feature planning review
- contract hardening review
- release validation pass
- Obsidian note curation workflow
- external reference capture workflow

## Layer 3: Knowledge notes

Knowledge notes hold durable context that should survive beyond one session.

This includes:

- architectural decisions
- good and bad prompt patterns
- external project references
- sample conversations worth reusing
- research notes about agent harnesses, skills, and workflow ideas

These notes are best treated as personal knowledge assets rather than as executable instructions.

## Why Obsidian matters

Obsidian is the right long-term home for much of this layer because it is:

- local-first
- easy to curate manually
- already part of the product's source model
- useful for linking notes, patterns, and references together

The CLI should not replace note-taking.
It should help search, retrieve, and operationalize those notes.

## Recommended Obsidian structure

The first useful note structure is:

- `Agents/`
- `Skills/`
- `Patterns/`
- `Sources/`
- `Experiments/`

Suggested meanings:

- `Agents/`: role notes, responsibilities, and decision heuristics
- `Skills/`: one note per reusable workflow or command pattern
- `Patterns/`: conversation structures, review patterns, prompt idioms, failure cases
- `Sources/`: curated notes from external projects such as `gstack`, `oh-my-openagent`, or other agent systems
- `Experiments/`: what was tried, what worked, what should be dropped

## Source-of-truth rule

The layers should have different source-of-truth expectations:

- repository docs define project behavior and delivery rules
- skill assets define reusable execution patterns
- Obsidian notes define personal research, examples, and curation history

Do not force all personal knowledge into repository docs.
Do not leave project-critical decisions only inside personal notes.

## `rfs-cli` responsibility

`rfs-cli` should help with this model in three ways:

1. index and search the notes
2. surface the right note or skill at the moment of need
3. later expose safe commands for listing and inspecting agent/skill assets

The CLI should support discovery and retrieval first.
It should not rush into a complex live skill registry or marketplace model.

## Future command direction

Possible future directions, after the model is validated:

- `rfs search` and `rfs show` working well against `Agents/` and `Skills/` notes
- `rfs research export` for curated skill/reference bundles
- a later `rfs agent` subcommand for listing role and skill records
- optional note templates for capturing external references and experiments

These should arrive incrementally, with retrieval and curation first.

## Non-goals

This model does not imply:

- a remote skill marketplace
- automatic execution of arbitrary third-party skills
- replacing repository docs with personal notes
- turning every note into a runtime command
- large multi-user knowledge management features

## Acceptance criteria

Before implementation starts, this model should satisfy all of these:

1. Agent roles, skills, and knowledge notes are clearly separated.
2. Obsidian is treated as a durable personal knowledge layer, not a replacement for repo docs.
3. `rfs-cli` is positioned first as a retrieval and curation tool for these assets.
4. Future command expansion stays local-first and incremental.

## Recommended next slices

1. Define a minimal note template for `Agents/`, `Skills/`, and `Sources/`.
2. Decide whether `rfs research export` should support curated skill/reference bundles directly.
3. Define a small read-only registry surface for agent and skill notes before any execution-oriented registry is considered.

The first note-template slice is documented in `docs/agent-note-templates.md`.
Curated skill/reference bundles should reuse the existing `rfs research export` format as documented in `docs/research-export-format.md`.
The first read-only registry surface is documented in `docs/agent-skill-registry-surface.md`.
