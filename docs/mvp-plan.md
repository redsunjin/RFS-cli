# MVP Plan

## MVP objective

Deliver a personally useful CLI that can:

- register local and Obsidian sources
- build and refresh a local index
- search indexed knowledge with practical filters
- inspect indexed documents with source metadata
- expose a small set of reliable agent-safe commands

The MVP is intentionally narrower than the full product roadmap. Google Drive, NotebookLM-adjacent exports, and richer external integrations remain post-MVP work.

## MVP scope

### Included

- `rfs index add`
- `rfs index sources`
- `rfs index run`
- `rfs search`
- `rfs show`
- `rfs dev git-summary`
- `rfs dev project-stats`
- `rfs dev find-todo`
- `rfs agent list-files`
- `rfs agent find-text`
- stable JSON output for user-facing and agent-facing commands in MVP scope

### Excluded

- Google Drive auth and search
- NotebookLM export automation
- advanced binary document extraction
- background sync or watch mode
- package publishing and release automation

## MVP acceptance criteria

### Knowledge workflow

- A user can register at least one Obsidian root and one local root
- A user can build an index without manual file editing
- Search supports text, source, tag, path prefix, and file type filtering
- `show` returns indexed metadata for indexed documents

### Developer workflow

- `dev git-summary` reports branch and working tree changes
- `dev project-stats` reports counts without scanning ignored directories
- `dev find-todo` finds TODO-like markers in bounded paths

### Agent workflow

- `agent` commands default to JSON output
- Command payloads include `schema_version`, `command`, `ok`, `data`, and `error`
- Failure modes return stable error codes and non-zero exit status

### Quality gate

- pytest passes
- Ruff passes
- fixture coverage exists for search, index, and show behavior
- docs are updated for scope changes

## MVP workstreams

### Workstream 1: Knowledge retrieval completion

- strengthen frontmatter parsing
- calibrate ranking
- improve indexed search filtering
- improve `show` inspection output

### Workstream 2: Developer utilities completion

- define `dev` command contract
- implement `dev find-todo`
- add tests for repository-oriented commands

### Workstream 3: Agent interface hardening

- normalize error codes and edge cases
- add contract tests for JSON outputs
- add bounded output safeguards

### Workstream 4: MVP release prep

- define install/run instructions
- add a smoke-test checklist
- ensure README examples match actual behavior

## Delivery sequence

1. Finish Workstream 1 because it is the core user value.
2. Finish Workstream 2 to validate the multi-domain CLI shape.
3. Finish Workstream 3 so the tool is dependable for AI use.
4. Finish Workstream 4 to make the MVP maintainable and repeatable.

## Exit definition

The MVP is complete when:

- the commands in MVP scope work end-to-end
- tests and lint pass consistently
- docs describe the actual shipped behavior
- the internal agent review loop has signed off on the last MVP milestone

See also:

- `docs/mvp-status.md` for current completion state
- `docs/smoke-checklist.md` for manual end-to-end verification
