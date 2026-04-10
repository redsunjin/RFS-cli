# Wiki Ingest Plan Contract

## Goal

Define the first reviewable contract for planning how a raw source should affect the compiled wiki.

This contract is for planning only.
It does not write wiki files yet.

## First command direction

- `rfs wiki plan-ingest <path-or-document-id>`

The command should accept either:

- a filesystem path to a raw source
- an indexed document id when the source is already in the local index

## Why planning comes first

- planning is safer than direct autonomous write-back
- the user can review proposed wiki mutations before any file changes happen
- the contract can be tested without needing a full wiki editor implementation
- the workflow matches the repository harness: plan, review, execute, verify

## First-version rules

- local-first only
- read-only against raw sources
- no silent wiki mutation
- output must stay bounded and reviewable
- the plan must distinguish create versus update actions
- the plan must call out contradictions and confidence gaps explicitly

## Required plan outputs

The first plan should answer these questions:

1. what source was read
2. what summary should be captured
3. which wiki pages should be created
4. which wiki pages should be updated
5. what contradictions, reinforcements, or unresolved questions were detected
6. what log entry should be appended if the plan is later applied

## Proposed text-mode structure

Human-readable output should stay compact and operational:

- source summary
- proposed page creates
- proposed page updates
- contradictions or unresolved items
- recommended next action

## Proposed JSON contract

The first safe JSON shape is:

- `schema_version`
- `command`
- `ok`
- `data.plan`
- `error`

`plan` should contain:

- `plan_id`
- `source_ref`
- `source_kind`
- `summary`
- `creates`
- `updates`
- `findings`
- `log_entry`
- `next_action`

### `source_ref`

`source_ref` should contain:

- `path` or `document_id`
- `title`
- `source_id` when available
- `source_type` when available

### `creates`

Each create item should contain:

- `path`
- `page_kind`
- `reason`
- `suggested_title`
- `outline`

### `updates`

Each update item should contain:

- `path`
- `reason`
- `change_summary`
- `sections_to_touch`

### `findings`

Each finding should contain:

- `kind`
  `contradiction`, `reinforcement`, `gap`, or `question`
- `summary`
- `related_pages`
- `severity`
  `low`, `medium`, or `high`

## Example JSON

```json
{
  "schema_version": "1",
  "command": "wiki_plan_ingest",
  "ok": true,
  "data": {
    "plan": {
      "plan_id": "wiki-plan-20260410-001",
      "source_ref": {
        "document_id": "note-123",
        "title": "Karpathy - LLM Wiki",
        "source_id": "vault",
        "source_type": "obsidian"
      },
      "summary": "Describes a compiled wiki pattern between raw sources and final answers.",
      "creates": [
        {
          "path": "wiki/concepts/compiled-wiki-layer.md",
          "page_kind": "concept",
          "reason": "This concept does not yet have a dedicated page.",
          "suggested_title": "Compiled Wiki Layer",
          "outline": [
            "Definition",
            "Layer Boundaries",
            "Why It Matters",
            "Open Questions"
          ]
        }
      ],
      "updates": [
        {
          "path": "wiki/overview.md",
          "reason": "The source changes the current knowledge-system framing.",
          "change_summary": "Add the compiled wiki layer between raw sources and query-time answers.",
          "sections_to_touch": [
            "Knowledge Architecture",
            "Operating Model"
          ]
        }
      ],
      "findings": [
        {
          "kind": "question",
          "summary": "The first directory conventions are not fixed yet.",
          "related_pages": [
            "wiki/overview.md"
          ],
          "severity": "medium"
        }
      ],
      "log_entry": "Plan ingest for Karpathy LLM Wiki source; create compiled-wiki-layer page and update overview.",
      "next_action": "Review the plan before applying wiki changes."
    }
  },
  "error": null
}
```

## Error direction

The first error set should stay small:

- `not_found`
- `missing_index`
- `unsupported_source`
- `invalid_wiki_state`

## Non-goals

- no direct file mutation
- no background ingestion queue
- no automatic source fetching
- no schema for rich page bodies yet
- no requirement that every finding be perfectly classified

## Recommended next slice

After this contract is accepted:

1. define the first wiki lint report contract
2. define the first directory and file conventions
3. only then consider runtime planning or apply commands
