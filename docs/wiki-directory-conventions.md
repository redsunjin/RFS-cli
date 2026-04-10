# Wiki Directory And File Conventions

## Goal

Define the first directory and file conventions for the compiled wiki layer.

These conventions are meant to keep the first version simple, local-first, reviewable, and compatible with ordinary Markdown tools such as Obsidian and git.

## Primary rule

The compiled wiki is content, not runtime state.

That means:

- do not store it under `.rfs/`
- do not treat it like a cache
- do not mix it with project-critical repository docs
- keep it in a user-visible Markdown workspace

## Recommended root layout

The first recommended layout is:

```text
<knowledge-root>/
  raw/
  wiki/
    index.md
    log.md
    overview.md
    concepts/
    entities/
    questions/
```

### `raw/`

- immutable source inputs
- clipped articles, notes, transcripts, exports, and other collected material
- never modified by wiki maintenance commands

### `wiki/`

- compiled synthesis layer
- edited only through reviewable wiki workflows or direct human edits
- searchable as ordinary Markdown content

## Required files

### `wiki/index.md`

Purpose:

- content-oriented catalog of wiki pages
- short summaries and grouping by page kind
- first navigation point before deeper wiki reads

Rules:

- must exist
- should stay human-readable
- should link to every maintained wiki page in the first version

### `wiki/log.md`

Purpose:

- append-only maintenance log
- record ingest plans, applies, lint passes, and important question-filing events

Rules:

- must exist
- should append rather than rewrite history
- each entry should begin with a stable heading pattern

Recommended heading pattern:

```md
## [2026-04-10] ingest | Karpathy LLM Wiki
```

### `wiki/overview.md`

Purpose:

- high-level orientation page
- short explanation of what the wiki covers, what its main sections are, and what is still incomplete

Rules:

- must exist
- should be the first human-facing landing page

## First subdirectories

### `wiki/concepts/`

- concept pages
- operating models
- frameworks
- recurring abstractions

Examples:

- `compiled-wiki-layer.md`
- `agent-knowledge-boundary.md`

### `wiki/entities/`

- named tools, systems, projects, organizations, or people
- one page per durable named thing when that thing matters across multiple sources

Examples:

- `obsidian.md`
- `notebooklm.md`

### `wiki/questions/`

- durable analysis pages created from important questions
- comparisons, tradeoff notes, and synthesized answers worth keeping

Examples:

- `how-rfs-cli-should-use-a-compiled-wiki.md`
- `comparing-local-knowledge-patterns.md`

## Optional future subdirectories

Do not require these in the first version, but allow them later if the wiki grows:

- `wiki/sources/`
- `wiki/timelines/`
- `wiki/people/`
- `wiki/experiments/`

## Naming rules

- use lowercase kebab-case filenames
- keep page names stable once linked from `index.md`
- prefer semantic names over dates in page filenames
- reserve dated headings for `log.md`, not for core concept pages

Examples:

- `compiled-wiki-layer.md`
- `knowledge-ingest-workflow.md`
- `karpathy-llm-wiki.md`

## Linking rules

- use relative Markdown links
- prefer direct page-to-page links over vague mentions
- add a link from `overview.md` or `index.md` for every newly created page
- when a page is updated because of a new source, add the source link or reference near the changed section when practical

## Source handling rules

- raw source files remain immutable
- compiled wiki pages may summarize, compare, or challenge source claims
- contradictions should be described in wiki pages and surfaced in lint output
- the wiki may cite raw sources, but it must not replace them as evidence

## State versus content boundary

Keep this boundary explicit:

- `.rfs/` is for machine state such as config, cache, token state, and indexes
- `wiki/` is for durable human-readable knowledge artifacts

This distinction matters because compiled wiki pages should be inspectable, editable, versionable, and portable outside the runtime state directory.

## Frontmatter rule

Do not require YAML frontmatter in the first version.

If frontmatter is added later, it should remain optional and lightweight.
The first version should work with headings and ordinary Markdown links alone.

## Recommended next slice

1. define the first small fixture set for wiki lint testing
2. decide whether `index.md` should require one-line page summaries in a fixed format
3. only then consider runtime implementation of `wiki plan-ingest` or `wiki lint`
