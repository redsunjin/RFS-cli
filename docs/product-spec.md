# Product Spec

## Product summary

`rfs-cli` is a command-line application for indexing, searching, inspecting, and summarizing personal knowledge and developer context. It is designed for both direct human usage and AI-agent execution, and it now includes guided CLI assistance so users can discover commands conversationally. The longer-term product direction is a CLI-native agent that can use its own tools while preserving a consistent style and bounded domain. That agent identity is now explicitly R2-D2-inspired and backed by a required LLM onboarding path. The current idea branch further emphasizes non-developer-friendly usage so the product can translate a task request into the right command instead of assuming the user already knows CLI structure.

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

### Non-expert guided operation

- Describe a task in plain language and get one recommended next step
- Receive command suggestions without understanding the full command tree first
- Use the same task-first flow for source registration, search, inspection, and diagnosis
- Allow task-first guidance to list connected sources and recall the most recent internal command when that is the safest next step
- See one obvious starting path before a full help dump in startup and shell help surfaces
- Recover from missing setup, missing index state, or empty results through short guidance
- Use startup, help, and shell flows that progressively reveal syntax only when needed
- Keep startup and shell help human-facing; only `ask --format json` guidance fields should be treated as public machine-readable contract

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
- As a non-developer user, I want to describe what I need in plain language and receive the right command to run.
- As a new user, I want the CLI to explain the next safe step after an error, empty state, or missing setup instead of only printing syntax.

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
- ground natural-language shell guidance in current source and index state
- use the same short follow-up behavior as `rfs ask` when a shell request is underspecified

Examples:

- `rfs shell`
- inside shell: `search roadmap`
- inside shell: `/run index sources`
- inside shell: `!git status`

### `rfs doctor`

Responsibilities:

- inspect workspace state under the selected `.rfs` directory
- report config, index, shell-memory, and LLM runtime health
- provide one local diagnostic entrypoint before deeper manual inspection
- support a verbose mode for richer local debugging details

Examples:

- `rfs doctor`
- `rfs doctor --verbose --format json`

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

- define and inspect the Google Drive source configuration
- run a local OAuth installed-app flow and persist Drive token state locally
- execute metadata-only Google Drive search through a cache-backed adapter
- keep the active Drive corpus explicit and limited to one supported corpus per config
- expose cache settings that keep remote behavior aligned with the local-first model

Examples:

- `rfs drive auth`
- `rfs drive status`
- `rfs drive search "proposal"`

### `rfs research`

Responsibilities:

- export curated indexed results into a portable local bundle
- write a stable `manifest.json` plus document files under `documents/`
- generate a query-based bundle directory automatically when `--output` is omitted
- keep the first export path local-first and NotebookLM-adjacent rather than provider-specific

Examples:

- `rfs research export "agent systems"`
- `rfs research export "agent systems" --output ./exports/agent-systems`
- `rfs research export "roadmap" --source obsidian --limit 5`

### Post-MVP external tool providers

Shared requirements:

- use one provider contract for registration, invocation mode, and confirmation policy
- keep provider capabilities explicit and separate read-only from state-changing actions
- normalize provider results before surfacing them through the CLI agent

NestClaw:

- API or CLI-backed orchestration tool provider
- focus first on `create`, `run`, `status`, `events`, and approval-oriented reads

qa_claw:

- script-backed workflow and verification tool provider
- focus first on worktree bootstrap, verification, and sprint-runbook execution helpers

### Post-MVP optional harbor layer

- an optional `rfs harbor` or similar TUI rest space
- short opt-in mini-games that do not block core workflows
- progression or reward state that stays separate from core CLI correctness
- one separate state file such as `.rfs/harbor.json`
- no reward or harbor mechanic should gate real CLI features

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
- translate plain-language task descriptions into actionable command suggestions
- ask one short follow-up question when the request is underspecified
- avoid inventing unsupported features
- evolve into the main human-facing agent entrypoint for guided tool usage

Examples:

- `rfs ask "How do I add my Obsidian vault?"`
- `rfs ask "How do I search only markdown files?"`

### Assistive help surfaces

Responsibilities:

- keep startup, `--help`, `ask`, and `shell` guidance aligned
- lead with one recommended command before listing alternatives
- explain missing setup or missing local state in plain Korean
- reveal advanced flags and subcommands progressively instead of dumping them first

Examples:

- `rfs`
- `rfs --help`
- inside shell: `내 노트에서 roadmap 찾아줘`

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
- Allow Drive-specific configuration and auth state to exist before live remote search is exposed

### Assistive UX requirements

- Accept task-oriented natural-language input in Korean by default
- Turn a user goal into one recommended command plus a short explanation
- Ask for only the single most important missing detail before proceeding
- Explain empty states and setup blockers in plain language instead of only showing raw syntax
- Return deterministic command suggestions for obvious missing-state cases such as missing index or diagnostics
- Use path hints, source-kind hints, shell-memory context, and doctor-visible state where they make the next step obvious
- Support deterministic guidance for connected-source listing and recent-command recall when shell-memory context is available
- Label deterministic recommendations as read-only or state-changing in user-facing guidance
- Keep guidance grounded in current config, index, shell, and doctor-visible state
- Distinguish between read-only suggestions and state-changing commands
- Keep existing JSON contracts stable unless an AI tooling review explicitly approves a new guidance payload
- Treat internal intent, suggestion, and help-block models as implementation detail unless explicitly promoted through contract review
- Make direct command empty states and setup blockers use short Korean-first recovery copy with one next step where practical
- Treat the current `ask` payload as sufficient for human-in-the-loop automation until a reviewed unattended-execution use case exists

## Idea-branch experimental modules

The current experimental track should stay behind existing entrypoints such as `rfs`, `rfs ask`, and `rfs shell`. It should not introduce a new top-level command until the behavior is validated.

### Intent interpreter

Responsibilities:

- normalize plain-language requests into a small internal intent model
- detect the likely task category and extract obvious entities
- distinguish categories such as add-source, search, inspect, and diagnose
- identify the one missing detail that blocks an actionable command

### Suggestion planner

Responsibilities:

- map an interpreted task plus runtime state to supported commands
- decide whether to suggest onboarding, indexing, search, inspection, or diagnostics first
- return deterministic suggestions before falling back to broader LLM wording when the state is clear
- rank one primary recommendation and one fallback

### Guidance renderer

Responsibilities:

- present one recommended command in a plain-language answer
- explain why the recommendation fits the task and local state
- keep the answer short and operational rather than chatty

### Search

- Support keyword search across indexed text
- Return ranked results with source, path, title, and snippet
- Support filters for source, file type, tag, and path prefix
- Support source-id filtering when multiple roots of the same source type exist
- Support Obsidian alias and frontmatter-aware retrieval

### Research export

- Export indexed search results into a bundle directory with `manifest.json` and `documents/`
- Preserve source metadata, paths, tags, aliases, content hash, and snippets in the manifest
- Allow the same source and metadata filters used by indexed search
- When `--output` is omitted, derive a filesystem-safe query-based bundle path that avoids the ambiguous `latest` naming pattern
- Keep the first implementation local-index-based and text-first

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
- Store Google Drive auth and cache boundary settings in the same local config file
- Store Google Drive token state in the workspace state directory
- Store Google Drive metadata cache state in the workspace state directory
- Treat LLM configuration as required for normal agent workflows

### Installation and release readiness

- Document a local development install flow with `uv sync --all-groups`
- Document a tool-style install flow with `uv tool install .`
- Document a Git-based install flow for a remote repository URL
- Document how to verify the install with `rfs --help` or `uv run rfs --help`
- Document how to verify local state with `rfs doctor --verbose`
- Document the workspace state directory and how to recover it when `.rfs/` becomes stale
- Document a pre-1.0 versioning policy and keep runtime/package versions aligned
- Maintain a release checklist that covers docs, tests, build, and runtime smoke

### Google Drive contract baseline

- Define a persisted Drive source config model
- Implement an OAuth-installed-app auth flow with local token persistence
- Implement read-only metadata retrieval against the Drive files API
- Implement a local metadata cache boundary for repeated Drive reads
- Expose live metadata-only `drive search` on top of the cached adapter

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
- Teach the agent that `rfs research export` is the portable handoff path for curated local results

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
