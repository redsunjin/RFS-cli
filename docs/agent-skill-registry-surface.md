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

For single-record role inspection, a short `responsibilities` list may also be exposed.

For single-record skill inspection, one short `example` field may also be exposed.

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

### Example: `list-notes`

```json
{
  "schema_version": "1",
  "command": "agent_list_notes",
  "ok": true,
  "data": {
    "kind": "role",
    "item_count": 1,
    "items": [
      {
        "id": "abc123def456",
        "name": "Product and Roadmap",
        "kind": "role",
        "purpose": "Keep scope aligned",
        "boundaries": ["Do not change runtime contracts alone"],
        "related_skills": ["Contract Hardening Review"],
        "path": "/path/to/Agents/product-roadmap.md"
      }
    ]
  },
  "error": null
}
```

### Example: `show-note`

```json
{
  "schema_version": "1",
  "command": "agent_show_note",
  "ok": true,
  "data": {
    "record": {
      "id": "def789ghi012",
      "name": "Release Validation Pass",
      "kind": "skill",
      "purpose": "Verify release readiness",
      "trigger": "Before a release cut",
      "constraints": ["No scope expansion"],
      "example": "uv run pytest -q",
      "related_agents": ["QA and Release"],
      "path": "/path/to/Skills/release-validation-pass.md"
    }
  },
  "error": null
}
```

### Example: `show-note` for a role record

```json
{
  "schema_version": "1",
  "command": "agent_show_note",
  "ok": true,
  "data": {
    "record": {
      "id": "abc123def456",
      "name": "Product and Roadmap",
      "kind": "role",
      "purpose": "Keep scope aligned",
      "boundaries": ["Do not change runtime contracts alone"],
      "responsibilities": ["Prioritize slices", "Keep roadmap in sync"],
      "related_skills": ["Contract Hardening Review"],
      "path": "/path/to/Agents/product-roadmap.md"
    }
  },
  "error": null
}
```

### Example: not found

```json
{
  "schema_version": "1",
  "command": "agent_show_note",
  "ok": false,
  "data": {},
  "error": {
    "code": "not_found",
    "message": "No agent or skill note found for id 'missing-id'."
  }
}
```

## Relationship to existing commands

This surface should come after basic retrieval is already working through:

- `rfs search`
- `rfs show`
- existing indexed note flows

It is a convenience layer over indexed notes, not a replacement for general search.

## `Sources/` note decision

For the first registry surface, `Sources/` notes should stay behind existing retrieval flows such as `rfs search` and `rfs show`.

Why:

- source notes are more exploratory and less standardized than role or skill notes
- role and skill notes are the higher-value structured assets for the first registry slice
- keeping `Sources/` search-only avoids widening the first extracted contract too early

`Sources/` notes can join the registry later if a stable extracted record shape becomes useful.

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

1. Keep implementation indexing-backed rather than adding a separate registry store.
2. Keep role and skill single-record enrichment small instead of widening list payloads.
3. Revisit `Sources/` notes only if a stable extracted view becomes necessary.
