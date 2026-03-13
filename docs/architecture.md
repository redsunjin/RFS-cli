# Architecture

## Overview

The system should be built as a modular CLI with a shared application core and separate source adapters. The architecture must support both human-readable terminal output and stable machine-readable output.

## Selected implementation stack

- Python 3.9+
- `uv` for project and dependency management
- Typer for command routing
- Pydantic for config and structured payload models
- Pytest for tests
- Ruff for linting

## High-level modules

### CLI layer

Responsibilities:

- parse commands and flags
- validate input
- dispatch use cases
- format output

### Application layer

Responsibilities:

- implement use-case orchestration
- apply business rules
- translate between adapters and output models
- provide guided command assistance backed by a configured LLM provider

### Domain layer

Responsibilities:

- define entities such as Source, Document, SearchResult, and IndexRecord
- define repository and service interfaces

### Infrastructure layer

Responsibilities:

- filesystem adapter
- Obsidian adapter
- Drive adapter
- LLM provider adapters for Ollama, LM Studio, and OpenAI-compatible APIs
- index storage
- git inspection service
- config persistence

## Proposed package layout

```text
src/
  cli/
  app/
  domain/
  infra/
  output/
tests/
docs/
```

## Phase 1 baseline note

The current baseline stores source configuration and a local JSON index under a workspace state directory. Human search flows now use the stored index, while bounded agent text search still supports direct live filesystem scanning.

The current index stores relative paths, file types, tags, aliases, and source-specific metadata for indexed documents. Obsidian notes use frontmatter-aware extraction.
The frontmatter parser supports a lightweight nested subset for practical note metadata such as lists, booleans, numbers, and simple nested maps.
The same workspace config now also stores optional LLM provider settings for conversational command guidance.

## Data model

### Source

- `id`
- `type`
- `root_path`
- `display_name`
- `status`

### Document

- `id`
- `source_id`
- `path`
- `relative_path`
- `title`
- `file_type`
- `content_hash`
- `modified_at`
- `aliases`
- `tags`
- `metadata`

### SearchResult

- `document_id`
- `score`
- `title`
- `path`
- `source_type`
- `snippet`

### LLMConfig

- `provider`
- `base_url`
- `model`
- `api_key_env`
- `enabled`

## Command flow

### Index flow

1. Load config
2. Resolve selected sources
3. Scan changed files
4. Extract metadata and text
5. Persist index records
6. Emit summary

### Search flow

1. Load config and index
2. Parse query and filters
3. Run search
4. Rank and shape result models
5. Render text or JSON

Search ranking is heuristic and currently combines title, alias, tag, path, content, and source-priority signals.

### Guided-help flow

1. Load config
2. Resolve configured LLM provider
3. Build a fixed prompt with the supported command catalog
4. Send the user question to the provider adapter
5. Return text or JSON with the answer payload

## Output contract strategy

Every command should expose:

- human mode for direct CLI use
- JSON mode with a versioned schema field

Example response shape:

```json
{
  "schema_version": "1",
  "command": "search",
  "ok": true,
  "results": []
}
```

## Error strategy

- Use structured error codes
- Return concise human messages in text mode
- Return `ok: false` with code and message in JSON mode
- Keep exit codes aligned with failure categories

## Integration design notes

### Obsidian adapter

- Focus first on Markdown notes and frontmatter
- Reuse filesystem scanning with Obsidian-specific metadata enrichment
- Ignore `.obsidian` workspace state files during note indexing

### Google Drive adapter

- Keep it isolated behind a source adapter boundary
- Add local caching so search behavior remains consistent with local sources

### Developer utility services

- Keep `dev` commands separate from knowledge indexing internals
- Share output formatting and config loading, but not index-specific logic
- Use a shared response shape for `dev` commands with `tool`, `subject_path`, and `summary`

### LLM provider services

- Keep provider-specific HTTP contracts isolated from CLI command handlers
- Use Ollama native chat for local Ollama runtimes
- Use OpenAI-compatible chat completions for LM Studio and generic compatible APIs
- Keep base commands usable when no provider is configured

## Test strategy

- Unit tests for command handlers and domain services
- Fixture-based tests for indexing and search behavior
- Contract tests for JSON output
- Integration tests for source adapters where practical
- Mocked tests for LLM setup, status, and guided-help command behavior
