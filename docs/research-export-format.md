# Research Export Format

## Goal

Define a local, predictable bundle format for handing indexed documents off into external research tools such as NotebookLM.
The same format may also be reused later for curated skill and reference note bundles drawn from indexed personal knowledge sources.

## Command surface

- `rfs research export "<query>"`

## Default output location

- `exports/research/<slug>-<timestamp>/`

The slug comes from the query text.
The timestamp uses UTC in `YYYYMMDD-HHMMSSZ` format.

## Bundle layout

- `manifest.json`
- `documents/<source_id>/<relative_path>`

## Manifest shape

`manifest.json` records:

- `schema_version`
- `bundle_type`
- `query`
- `exported_at`
- `state_dir`
- `filters`
- `document_count`
- `documents`

Each document entry records:

- `document_id`
- `title`
- `source_id`
- `source_type`
- `relative_path`
- `export_path`
- `file_type`
- `tags`
- `aliases`
- `metadata`
- `content_source`

## Export rules

- Only indexed documents are eligible for export
- Query selection reuses the existing indexed search behavior and filters
- Export copies the current source file when it still exists
- If the source file is missing, export falls back to the indexed content snapshot
- The first slice is local and read-only; it does not add remote sync or NotebookLM automation

## Skill and reference bundle decision

`rfs research export` should also support curated skill and reference bundles when those assets are stored as indexed notes.

In the first version of that expansion:

- reuse the same command surface
- reuse the same bundle layout
- reuse the same manifest shape
- do not add a new skill-specific export command
- do not add a separate bundle schema only for agent or skill notes

This keeps export behavior consistent across ordinary research documents and curated personal agent knowledge.

## JSON command payload

The command returns a standard payload with:

- `query`
- `bundle_name`
- `exported_at`
- `state_dir`
- `filters`
- `document_count`
- `export_dir`
- `manifest_path`
- `documents`

## Intended use

This format is meant for:

- curating a small search-derived document set
- preserving source metadata and relative paths
- handing the bundle to adjacent research workflows without making NotebookLM the system of record
- packaging curated `Agents/`, `Skills/`, or `Sources/` notes when they are already indexed as local knowledge
