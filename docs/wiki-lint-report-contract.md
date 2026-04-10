# Wiki Lint Report Contract

## Goal

Define the first report contract for checking the health of the compiled wiki.

This command is meant to inspect the wiki layer, not to repair it automatically.

## First command direction

- `rfs wiki lint`

The first version should inspect the wiki directory and return a bounded report.

## Why lint matters

- a compiled wiki decays unless contradictions and stale pages are surfaced
- linting provides value before heavy automation exists
- the report gives the user and later agents a safe maintenance entrypoint

## First-version rules

- read-only only
- no automatic file edits
- local-first only
- bounded issue count
- issues must link back to concrete pages
- output should help choose the next maintenance action

## First issue categories

The first lint pass should look for:

- `contradiction`
- `stale_claim`
- `orphan_page`
- `missing_crosslink`
- `missing_page`
- `coverage_gap`

## Proposed text-mode structure

Human-readable output should contain:

- wiki summary
- issue counts by category
- highest-priority findings
- one recommended next action

## Proposed JSON contract

The first safe JSON shape is:

- `schema_version`
- `command`
- `ok`
- `data.report`
- `error`

`report` should contain:

- `wiki_root`
- `generated_at`
- `page_count`
- `issue_count`
- `issues_by_kind`
- `issues`
- `recommended_action`

Each issue should contain:

- `id`
- `kind`
- `severity`
- `path`
- `summary`
- `details`
- `related_paths`

## Example JSON

```json
{
  "schema_version": "1",
  "command": "wiki_lint",
  "ok": true,
  "data": {
    "report": {
      "wiki_root": "/path/to/wiki",
      "generated_at": "2026-04-10T14:00:00Z",
      "page_count": 12,
      "issue_count": 3,
      "issues_by_kind": {
        "missing_page": 1,
        "orphan_page": 1,
        "coverage_gap": 1
      },
      "issues": [
        {
          "id": "lint-001",
          "kind": "missing_page",
          "severity": "medium",
          "path": "wiki/overview.md",
          "summary": "The overview references a compiled wiki layer page that does not exist yet.",
          "details": "A direct link target is missing for the referenced concept.",
          "related_paths": [
            "wiki/concepts/compiled-wiki-layer.md"
          ]
        }
      ],
      "recommended_action": "Create the missing compiled wiki layer page before expanding query workflows."
    }
  },
  "error": null
}
```

## Bounded output rules

- return at most one summary object
- return issue counts for all categories
- cap detailed issues in the first version
- prefer highest-severity issues first
- do not dump full page contents into the report

## Error direction

The first error set should stay small:

- `wiki_missing`
- `invalid_wiki_state`
- `not_configured`

## Non-goals

- no automatic contradiction resolution
- no link rewriting
- no page creation
- no source re-ingestion
- no remote validation

## Recommended next slice

After this contract is accepted:

1. define the first wiki directory and file conventions
2. define the first small fixture set for wiki lint testing
3. only then consider runtime lint implementation
