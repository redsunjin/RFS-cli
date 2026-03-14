# Research Export Format

## Date

2026-03-15

## Purpose

This document defines the first `research export` bundle format for `rfs-cli`.
The goal is to package indexed local knowledge into a portable, reviewable bundle that can be reused in external research workflows such as NotebookLM-adjacent preparation.

## Format overview

A research export is a directory with:

- `manifest.json`
- `documents/`

Example:

```text
exports/
  research/
    roadmap-20260315-120000Z/
      manifest.json
      documents/
        01-project-roadmap.md
        02-agent-systems.md
```

## Manifest contract

`manifest.json` contains:

- `schema_version`
- `export_kind`
- `created_at`
- `query`
- `filters`
- `item_count`
- `documents`

## Document record contract

Each item under `documents` contains:

- `document_id`
- `title`
- `source_id`
- `source_type`
- `relative_path`
- `original_path`
- `export_path`
- `file_type`
- `snippet`
- `tags`
- `aliases`
- `metadata`
- `modified_at`
- `content_hash`

## Current behavior

- export is based on the existing local index, not direct filesystem rescans
- document files contain the indexed document content
- bundles are metadata-plus-content packages intended for curation and handoff
- search remains bounded by the existing `search_index` result model and filters
- if `--output` is omitted, a default bundle path is generated under `exports/research/<query-slug>-<timestamp>/`
- explicit `--output` still takes precedence when the user wants a fixed destination

## Current command shape

```bash
rfs research export "<query>"
rfs research export "<query>" --output ./exports/my-bundle
```

Supported filters:

- `--source`
- `--source-id`
- `--tag`
- `--path-prefix`
- `--file-type`
- `--limit`

## Design constraints

- keep the export format filesystem-friendly and inspectable without extra tooling
- keep the manifest stable enough for later agent or NotebookLM-adjacent workflows
- keep default bundle names clear enough that users can recognize the export without renaming it first
- avoid introducing remote sync assumptions
- keep the first format text-first and JSON-manifest-first

## Not included yet

- multi-query bundle plans
- document-body transformation or summarization
- Drive document export
- direct NotebookLM upload automation
