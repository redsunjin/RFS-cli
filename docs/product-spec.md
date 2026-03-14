# Product Spec

## Product summary

`rfs-cli` is a command-line application for indexing, searching, inspecting, and summarizing personal knowledge and developer context. It is designed for both direct human usage and AI-agent execution, and it now includes guided CLI assistance so users can discover commands conversationally. The longer-term product direction is a CLI-native agent that can use its own tools while preserving a consistent style and bounded domain. That agent identity is now explicitly R2-D2-inspired and backed by a required LLM onboarding path.

## MVP definition

The MVP covers local and Obsidian indexing, indexed search, indexed document inspection, baseline developer utilities, and reliable agent-safe JSON commands. Remote integrations such as Google Drive are explicitly deferred until after MVP completion.
Local companion projects such as NestClaw and qa_claw are also deferred until after MVP as external tool providers rather than core built-in domains.

## Core use cases

### Knowledge retrieval

- Search Obsidian notes by keyword, phrase, tag, or path
- Search Obsidian frontmatter metadata such as aliases and declared tags
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

### Guided CLI usage

- Configure a required local or remote LLM provider
- Ask the CLI how to perform a task without already knowing the command syntax
- Validate local provider connectivity before relying on guided help
- Use an interactive shell session instead of repeating one-shot commands
- Start with `rfs` alone in an interactive terminal and let the CLI choose onboarding or shell entry

### Agent behavior

- Present one coherent operator instead of a loose collection of commands
- Preserve a consistent tone and task-focused style
- Ground suggestions in real commands, local state, and available sources
- Ask short follow-up questions when a user request is ambiguous
- Use an R2-D2-inspired agent persona without drifting into roleplay or losing technical clarity
- Strip provider-specific reasoning tags or control markers before showing answers to the user

## User stories

- As a user, I want to search my Obsidian vault so I can retrieve notes quickly.
- As a user, I want to search local folders from one command so I do not have to remember where content lives.
- As a user, I want Google Drive search later without changing the top-level command model.
- As a developer, I want quick repository summaries from the same CLI.
- As an AI agent, I want stable JSON output so I can call the tool reliably.
- As a user, I want to ask the CLI what command to run so I do not have to memorize the command tree.
- As a user, I want the CLI to behave like one assistant with a recognizable style, not just a help page.
- As a user, I want the CLI to ask for only the missing detail when my request is underspecified.
- As a user, I want to stay inside a shell session where previous commands and answers are remembered.
- As a user, I want onboarding to configure the required LLM first so the agent works from the start.

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

### `rfs shell`

Responsibilities:

- keep the user inside an interactive CLI session
- run supported `rfs` commands without repeating the top-level executable name
- store conversation and tool history as shell memory
- support controlled external CLI execution when explicitly requested

Examples:

- `rfs shell`
- inside shell: `search roadmap`
- inside shell: `/run index sources`
- inside shell: `!git status`

### `rfs` startup behavior

Responsibilities:

- detect interactive startup without an explicit subcommand
- launch onboarding automatically when no LLM is configured
- launch the interactive shell automatically when the CLI is already configured
- keep non-interactive invocation predictable by showing help text instead of blocking

Examples:

- `rfs`
- `rfs --state-dir ~/.rfs-work`

### `rfs dev`

Responsibilities:

- git status summary
- project file statistics
- TODO or log scanning
- return a consistent developer-tool payload with tool id, subject path, and summary

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

### Post-MVP external tool providers

- NestClaw: API or CLI-backed orchestration tool provider
- qa_claw: script-backed workflow and verification tool provider

### `rfs llm`

Responsibilities:

- configure the preferred LLM provider interactively
- report connection health and available models
- prepare future semantic or summarization workflows without making them mandatory for installation

Examples:

- `rfs llm setup`
- `rfs llm status`

### `rfs init`

Responsibilities:

- provide the first required onboarding path
- configure the LLM provider before other agent workflows
- expose the onboarding guide that teaches the agent its own command model

Examples:

- `rfs init`
- `rfs init --provider ollama`
- `rfs`

### `rfs ask`

Responsibilities:

- answer CLI usage questions conversationally
- recommend concrete supported commands
- ask one short follow-up question when the request is underspecified
- avoid inventing unsupported features
- evolve into the main human-facing agent entrypoint for guided tool usage

Examples:

- `rfs ask "How do I add my Obsidian vault?"`
- `rfs ask "How do I search only markdown files?"`

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
- Support source-id filtering when multiple roots of the same source type exist
- Support Obsidian alias and frontmatter-aware retrieval

### Content inspection

- Show metadata such as modified time, source type, and file size
- Show indexed tags, aliases, and relative source path when available
- Show a bounded content preview
- Resolve records by ID or direct path

### Output modes

- Default text output for humans
- JSON output for automation
- Predictable schemas per command

### Configuration

- Store source roots and preferences in a local config file
- Support environment variable overrides where useful
- Store LLM provider settings in the same local config file
- Treat LLM configuration as required for normal agent workflows

### Guided assistance

- Support `ollama`, `lmstudio`, and generic OpenAI-compatible HTTP providers
- Provide interactive setup with sensible local defaults for provider base URLs
- Expose a provider status command that checks reachability and visible model IDs
- Allow `rfs ask` to work from a configured provider and answer with current supported commands only
- Incorporate current source configuration and index availability into command suggestions by default
- Use a short deterministic follow-up path before provider guidance when critical detail is missing
- Persist shell session memory so later turns can stay grounded in earlier interaction
- Load a dedicated onboarding document into the agent prompt so the LLM learns the CLI's actual usage model
- Load a dedicated agent contract into the prompt so response style and boundaries stay stable

### Agent identity

- Maintain a stable, pragmatic, tool-oriented response style
- Keep the CLI identity distinct from generic chat assistants
- Prefer doing or recommending concrete tool actions over broad discussion
- Keep the agent within the product domain of knowledge retrieval, project workflows, and tool execution
- Apply an R2-D2-inspired persona in a restrained, operational way
- Strip provider-specific reasoning tags and control markers before surfacing an answer

## Non-functional requirements

- Fast enough for interactive local search
- Safe path handling and bounded filesystem access
- Clear errors and non-zero exit codes on failure
- Testable modules with deterministic behavior
- Extensible source adapter model
- LLM connectivity is required for the full agent workflow, but direct failure messages must keep the first setup path obvious
- The conversational layer must not obscure direct command access
- External command execution must stay explicit and user-triggered

## Design constraints

- Avoid tight coupling between source connectors and search engine logic
- Prefer local index storage over repeated on-demand scans
- Keep command names short and memorable
- Do not make remote integrations a prerequisite for the MVP

## Risks

- Google Drive integration introduces auth and sync complexity
- Extracting useful text from mixed file formats may require staged support
- Search quality can degrade if metadata and ranking are not modeled early
- LLM-guided help can mislead users if prompts or command catalogs drift from the implemented CLI
- Agent persona can become inconsistent if style and scope are not defined as product contracts

## Deferred decisions

- Search backend choice
- Index storage technology
- File type extraction policy beyond Markdown and plain text
- Degree of NotebookLM workflow automation
- Depth of multi-turn agent interaction before introducing a dedicated interactive mode
