# Product Spec

## Product summary

`rfs-cli` is a command-line application for indexing, searching, inspecting, and summarizing personal knowledge and developer context. It is designed for both direct human usage and AI-agent execution.

## Core use cases

### Knowledge retrieval

- Search Obsidian notes by keyword, phrase, tag, or path
- Search local files by name, metadata, or extracted text
- View a result with key metadata and content preview
- Re-index selected roots when source content changes

### Developer workflows

- Summarize git repository state
- List project statistics such as file counts or language breakdown
- Find TODO markers, logs, or notable files

### Agent tooling

- List files in a bounded path
- Search text with structured result records
- Return normalized JSON for downstream AI usage
- Fail safely with machine-readable error output

## User stories

- As a user, I want to search my Obsidian vault so I can retrieve notes quickly.
- As a user, I want to search local folders from one command so I do not have to remember where content lives.
- As a user, I want Google Drive search later without changing the top-level command model.
- As a developer, I want quick repository summaries from the same CLI.
- As an AI agent, I want stable JSON output so I can call the tool reliably.

## Command model

### `rfs index`

Responsibilities:

- register source roots
- scan files
- extract metadata
- build or refresh a local index

Examples:

- `rfs index add ~/vault --source obsidian`
- `rfs index run`
- `rfs index run --source obsidian`

### `rfs search`

Responsibilities:

- full-text search
- filename search
- tag or metadata filtering
- ranked result listing

Examples:

- `rfs search "agent memory"`
- `rfs search "roadmap" --source obsidian`
- `rfs search "todo" --format json`

### `rfs show`

Responsibilities:

- display result details
- show metadata, path, snippets
- optionally render raw content

Examples:

- `rfs show note-123`
- `rfs show /path/to/file.md`

### `rfs dev`

Responsibilities:

- git status summary
- project file statistics
- TODO or log scanning

Examples:

- `rfs dev git-summary`
- `rfs dev project-stats`
- `rfs dev find-todo`

### `rfs drive`

Responsibilities:

- authenticate configured Google Drive access
- search remote file metadata and selected synced content
- optionally cache search results locally

Examples:

- `rfs drive auth`
- `rfs drive search "proposal"`

### `rfs agent`

Responsibilities:

- expose AI-safe utility commands
- guarantee bounded, structured output
- normalize errors and exit codes

Examples:

- `rfs agent list-files ./docs --format json`
- `rfs agent find-text "TODO" ./src --format json`

## Functional requirements

### Source management

- Support multiple indexed roots
- Tag each root with a source type such as `local`, `obsidian`, or `drive`
- Allow re-index by source or path

### Search

- Support keyword search across indexed text
- Return ranked results with source, path, title, and snippet
- Support filters for source, file type, tag, and path prefix

### Content inspection

- Show metadata such as modified time, source type, and file size
- Show a bounded content preview
- Resolve records by ID or direct path

### Output modes

- Default text output for humans
- JSON output for automation
- Predictable schemas per command

### Configuration

- Store source roots and preferences in a local config file
- Support environment variable overrides where useful

## Non-functional requirements

- Fast enough for interactive local search
- Safe path handling and bounded filesystem access
- Clear errors and non-zero exit codes on failure
- Testable modules with deterministic behavior
- Extensible source adapter model

## Design constraints

- Avoid tight coupling between source connectors and search engine logic
- Prefer local index storage over repeated on-demand scans
- Keep command names short and memorable
- Do not make remote integrations a prerequisite for the MVP

## Risks

- Google Drive integration introduces auth and sync complexity
- Extracting useful text from mixed file formats may require staged support
- Search quality can degrade if metadata and ranking are not modeled early

## Deferred decisions

- Search backend choice
- Index storage technology
- File type extraction policy beyond Markdown and plain text
- Degree of NotebookLM workflow automation
