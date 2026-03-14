# Architecture

## Overview

The system should be built as a modular CLI with a shared application core and separate source adapters. The architecture must support both human-readable terminal output and stable machine-readable output. It should also support a CLI-native agent layer that helps users operate the tool without turning the system into a generic chatbot. That agent layer now assumes a configured LLM and a packaged onboarding document as part of the normal startup path.

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
- enforce agent behavior rules such as style, domain boundaries, and grounding to implemented commands

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
- packaging and distribution metadata

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
The same workspace config now also stores required LLM provider settings for conversational command guidance.
The current implementation exposes one-shot guided help through `rfs ask`, an interactive `rfs shell` loop that saves shell memory under the workspace state directory, an `rfs init` onboarding path, and a default `rfs` startup flow that chooses onboarding or shell automatically in interactive terminals.

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

### ShellMemory

- `session_id`
- `created_at`
- `updated_at`
- `events`

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
3. Load the packaged onboarding guide and agent contract
4. Build runtime guidance context from configured sources and index state
5. Run deterministic ambiguity checks for missing source, path, or target details
6. If the question is underspecified, return one short follow-up question without calling the provider
7. Otherwise send the user question plus runtime context to the provider adapter
8. Sanitize provider-specific reasoning or control tokens from the answer
9. Return text or JSON with the answer payload

### Init flow

1. Start `rfs init`
2. Prompt for provider, base URL, model, and API-key environment variable where needed
3. Persist the LLM configuration to the workspace state directory
4. Present the onboarding guide that teaches the agent its own command surface
5. Hand off to `rfs llm status` or `rfs shell`

### Startup flow

1. Start `rfs` without a subcommand
2. Detect whether the session is interactive
3. If the session is non-interactive, render help text and exit
4. If no LLM config exists, launch onboarding automatically
5. If LLM config exists, launch the interactive shell automatically

### Planned agent-interaction flow

1. Inspect the current workspace state such as configured sources and index availability
2. Interpret the user goal through the agent policy and command catalog
3. If enough information exists, recommend or trigger the most relevant command path
4. If key information is missing, ask one short follow-up question
5. Keep the final guidance grounded in supported commands and observable state

### Current shell flow

1. Start `rfs shell`
2. Load or create persisted shell memory from `.rfs/shell-memory.json`
3. Accept one of:
   - direct `rfs` command input
   - `/run ...` internal command execution
   - `!<command>` external CLI execution
   - natural-language guidance request
4. Attach shell-session context so the agent knows the user is already inside the shell
5. Attach workspace-state guidance context so shell answers can adapt to configured sources and index state
6. Run deterministic ambiguity checks before provider guidance when critical detail is missing
7. Save conversation and tool output back into shell memory

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

### External tool provider adapters

- Treat NestClaw as a future provider behind an API or CLI adapter boundary
- Treat qa_claw as a future provider behind a script-runner adapter boundary
- Keep both outside the core MVP command surface until the current CLI agent baseline is complete

### Developer utility services

- Keep `dev` commands separate from knowledge indexing internals
- Share output formatting and config loading, but not index-specific logic
- Use a shared response shape for `dev` commands with `tool`, `subject_path`, and `summary`

### LLM provider services

- Keep provider-specific HTTP contracts isolated from CLI command handlers
- Use Ollama native chat for local Ollama runtimes
- Use OpenAI-compatible chat completions for LM Studio and generic compatible APIs
- Keep base commands usable when no provider is configured

### Agent policy services

- Keep a fixed product-domain prompt that limits the assistant to implemented capabilities
- Separate provider transport from agent style and grounding rules
- Prefer deterministic command recommendation over open-ended discussion
- Allow future expansion to a dedicated interactive mode without rewriting the command layer
- Keep shell memory as explicit persisted state instead of hidden in-process memory only
- Load onboarding documentation into the system prompt so agent behavior stays aligned with the implemented CLI
- Load a dedicated agent contract into the system prompt so persona and boundaries stay stable
- Feed `rfs ask` a workspace-state summary so recommendations can adapt to configured sources and index state
- Keep the R2-D2-inspired persona restrained and operational rather than theatrical

## Test strategy

- Unit tests for command handlers and domain services
- Fixture-based tests for indexing and search behavior
- Contract tests for JSON output
- Integration tests for source adapters where practical
- Mocked tests for LLM setup, status, and guided-help command behavior

## Packaging and install notes

- Development usage should continue to rely on `uv sync --all-groups` plus `uv run rfs ...`
- Tool-style installation should rely on `uv tool install .` or a Git URL install path
- Runtime prompt assets such as onboarding and agent-contract documents must remain included in the built wheel
