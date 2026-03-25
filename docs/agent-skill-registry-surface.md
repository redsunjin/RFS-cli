# Agent Skill Registry Surface

## Goal

Define the first read-only registry surface for agent and skill notes.

The purpose of this surface is discovery, not execution.

## First-version rule

The first registry surface should be:

- local-first
- read-only
- note-backed
- safe for JSON output
- narrow enough to validate without turning notes into executable plugins

## What the surface is for

The first registry surface should help a user or local agent:

- list known agent-role notes
- list known skill notes
- inspect a short summary of one note-backed record
- find related notes or linked assets

It should not execute skills or mutate note state.

## First implemented slice

The first implemented CLI slice should stay narrow:

- `rfs agent list-notes --kind role`
- `rfs agent list-notes --kind skill`
- `rfs agent show-note <id>`

## Minimal record shape

The first extracted record should be intentionally small.

For role notes:

- `id`
- `name`
- `kind`
- `purpose`
- `boundaries`
- `related_skills`
- `path`

For skill notes:

- `id`
- `name`
- `kind`
- `purpose`
- `trigger`
- `constraints`
- `related_agents`
- `path`

The source of these fields should be the note templates, not a new independent registry database.

## Source of truth

The registry surface should read from note content that already exists in Obsidian-backed sources.

That means:

- notes stay the source of truth
- registry output is an extracted view
- missing fields should degrade gracefully
- the first version should not require a dedicated sync step

## Safety rules

- no arbitrary skill execution
- no remote registry lookup
- no hidden state mutation
- no write-back to notes
- no requirement that every note be perfectly structured before it can be discovered

## JSON contract direction

If JSON output is added later, it should remain narrow and stable.

The first safe shape is:

- list command returns `items`
- show command returns one `record`
- each record contains only summary fields plus `path`

Do not expose raw private note history, hidden prompts, or execution metadata by default.

## Relationship to existing commands

This surface should come after basic retrieval is already working through:

- `rfs search`
- `rfs show`
- existing indexed note flows

It is a convenience layer over indexed notes, not a replacement for general search.

## Non-goals

This surface does not include:

- skill execution
- approval flows
- parameterized tool invocation
- background task orchestration
- automatic note generation
- marketplace or installation behavior

## Acceptance criteria

Before implementation starts, this surface should satisfy all of these:

1. The first commands are read-only only.
2. Notes remain the source of truth.
3. The extracted record shape is small and stable.
4. General note retrieval through `search` and `show` still remains valid.

## Recommended next slices

1. Define one exact JSON payload example for list and show in the docs.
2. Keep implementation indexing-backed rather than adding a separate registry store.
3. Decide whether `Sources/` notes should join the same registry surface or stay search-only longer.
