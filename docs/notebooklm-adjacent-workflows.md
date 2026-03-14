# NotebookLM-Adjacent Workflows

## Purpose

This document describes practical handoff patterns from `rfs-cli` into external research workflows such as NotebookLM.

It intentionally stops at local bundle preparation.
It does not define direct upload automation or any provider-specific UI flow.

## Core idea

Use `rfs research export` to create a small, reviewable bundle before moving material into an external research tool.

That bundle gives you:

- the selected document files
- a `manifest.json` with source and metadata context
- a stable local folder you can inspect before handoff

## Workflow 1: Export a focused topic bundle

Use this when you already know the topic you want to explore.

```bash
rfs research export "agent systems"
```

This creates a query-based bundle under:

```text
./exports/research/<query-slug>-<timestamp>/
```

Then:

1. inspect `manifest.json`
2. remove or keep files you want to hand off
3. move the selected document files into your next research step

## Workflow 2: Export from one source only

Use this when your local vault and filesystem notes should stay separated.

```bash
rfs research export "roadmap" --source obsidian
```

This keeps the bundle aligned to one source type and makes later review simpler.

## Workflow 3: Export a narrower curation set

Use source metadata filters when the first search is still too broad.

```bash
rfs research export "agent" --tag agents --path-prefix ideas --limit 5
```

This is the preferred path when you want a smaller handoff set for external reading or summarization.

## Workflow 4: Use a fixed output path for a named handoff

Use this when the destination path matters more than the generated default name.

```bash
rfs research export "weekly roadmap" --output ./exports/research/weekly-roadmap-review
```

Choose this form when:

- the bundle belongs to a recurring review
- the folder will be referenced in another local workflow
- you want a durable path that is not timestamp-based

## Review checklist before handoff

Check these before using the bundle elsewhere:

- the query matches the intended topic
- the document count is small enough to review
- the document titles and snippets look relevant
- the bundle contains no files you do not want to carry forward
- the manifest still reflects the filters you intended

## Recommended handoff boundary

`rfs-cli` should handle:

- local indexing
- local search and filtering
- local export bundle creation

The external research tool should handle:

- later reading
- note comparison
- downstream synthesis

## Not included

- direct NotebookLM upload
- provider-specific browser automation
- automatic bundle cleanup after handoff
- document rewriting during export
