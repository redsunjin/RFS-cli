# Wiki Maintenance Model

## Goal

Define a future compiled wiki layer for `rfs-cli` that accumulates synthesized knowledge in local Markdown instead of forcing the LLM to re-derive the same synthesis from raw sources on every query.

This model is inspired by the "LLM Wiki" pattern described by Andrej Karpathy in April 2026:

- [Karpathy: LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

## Core idea

The model has three layers:

1. raw sources
2. compiled wiki
3. maintenance schema

### Raw sources

- immutable inputs
- articles, notes, papers, transcripts, exports, local files
- source of truth for what was actually observed

### Compiled wiki

- LLM-maintained Markdown pages
- summaries, entity pages, concept pages, comparisons, timelines, synthesis notes
- updated incrementally as new sources arrive or important questions are answered

### Maintenance schema

- the rules that tell the LLM how the wiki should be organized and maintained
- page naming rules, ingest rules, cross-link expectations, contradiction handling, review workflow, and logging rules

## Why this fits `rfs-cli`

`rfs-cli` already has several pieces needed for this pattern:

- local-first source registration and indexing
- Obsidian-friendly Markdown retrieval
- a note-backed personal knowledge model
- `rfs search`, `rfs show`, and `rfs research export`
- a documentation-first harness for reviewable changes

What is missing is a compiled synthesis layer between the raw sources and the final answer.

## Layer boundaries

The boundaries must stay strict:

- raw sources are not modified by the wiki workflow
- project-critical repo docs are not treated as personal wiki pages
- compiled wiki pages are editable outputs, not source-of-truth evidence
- note registries and skill registries remain separate from the wiki maintenance flow

## First directory shape

The first useful shape is intentionally small:

```text
wiki/
  index.md
  log.md
  overview.md
  entities/
  concepts/
  questions/
```

This is a content suggestion, not a fixed runtime requirement yet.

The current directory and file conventions are now documented in `docs/wiki-directory-conventions.md`.

## First operations

### Ingest

Read one new raw source, summarize it, decide which wiki pages should be created or updated, identify contradictions or reinforcements, and record the action in the log.

### Query

Answer a question by reading the compiled wiki first, then drilling into raw sources only when the wiki is missing support or needs verification.

### Lint

Inspect the wiki for:

- stale claims
- contradictions
- orphan pages
- missing cross-links
- concepts that are referenced but do not yet have a page
- gaps that should trigger more source collection

## First safe CLI direction

The first slice should stay reviewable:

- `rfs wiki plan-ingest <path|document-id>`
- `rfs wiki apply-ingest <plan-id|path>`
- `rfs wiki lint`

Why this order:

- planning is safer than direct write-back
- review fits the existing work harness
- linting provides value even before heavy automation exists

## Design rules

- keep everything local-first
- use ordinary Markdown files
- prefer git-visible file changes
- keep the first version human-reviewable
- do not silently mutate the wiki during normal chat
- do not mix project repo docs with personal wiki pages
- use the existing index/search stack before adding a new retrieval subsystem

## Relationship to current note tracks

- `Agents/`, `Skills/`, and `Sources/` notes remain curated personal knowledge notes
- the compiled wiki is a separate synthesized layer
- `Sources/` notes can reference raw sources and wiki pages, but they should not replace either layer

## Non-goals

This model does not imply:

- autonomous background wiki mutation without review
- a remote multi-user wiki service
- replacing `rfs search` or `rfs show`
- replacing repo docs with LLM-written notes
- automatic execution of skills from wiki pages

## Recommended first slice

1. define the wiki maintenance schema and file conventions
2. define a reviewable ingest plan shape
3. define a lint report shape

Only after that should runtime commands be considered.

The first contract documents are:

- `docs/wiki-ingest-plan-contract.md`
- `docs/wiki-lint-report-contract.md`
- `docs/wiki-directory-conventions.md`
