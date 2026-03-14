# Project Charter

## Mission

Build a personal CLI agent that unifies knowledge retrieval, developer utilities, and AI-tool execution into one consistent interface.

## Why this project exists

The project is primarily a learning vehicle, but it must also become a real tool that is useful in daily work. The CLI should reduce friction when searching notes, inspecting files, summarizing project state, and providing reliable tool output for AI agents. It should also evolve beyond a loose command set into a single, recognizable agent that can use its own tools while keeping a consistent interaction style.

## Primary outcomes

- Make personal knowledge easy to search across Obsidian and local documents
- Provide a practical CLI foundation for future integrations such as Google Drive
- Create AI-safe command contracts with deterministic JSON output
- Add guided CLI usage so command discovery does not depend on memorizing syntax
- Turn the CLI into a tool-using agent with a stable voice and clear operating boundaries
- Require an LLM-backed onboarding path so the agent is configured before normal use
- Make `rfs` itself the easiest interactive entry point, not just a banner plus help page
- Keep the conversational agent aligned to a documented persona and response-style contract
- Define installation, verification, and recovery paths so the CLI is dependable outside the dev loop
- Provide a simple diagnostic path so broken local state can be inspected without guesswork
- Establish a documentation-driven development process from the beginning

## Problem statement

Personal knowledge and project context are fragmented across multiple systems:

- Obsidian vaults
- Local folders
- Google Drive
- External research workflows such as NotebookLM

The current friction is not only data access, but also the lack of one stable interface that both a human and an AI tool can use consistently.
There is also a usability gap: even if the CLI has the right features, it is easy to underuse them when the command model is not discoverable at the moment of need.
Finally, most CLIs expose tools but do not behave like a coherent operator. This project aims to close that gap.

## Product vision

`rfs-cli` becomes a local command center and CLI-native agent for:

- knowledge discovery
- file inspection
- developer workflow support
- agent tool execution
- interactive, LLM-assisted command guidance
- consistent, recognizable interaction
- a shell mode that keeps context and tool history across turns

## Target users

- Primary: the project owner
- Secondary: local AI agents that need safe filesystem and search capabilities

## Scope

### In scope

- Local filesystem indexing and search
- Obsidian vault indexing and search
- Content display and metadata inspection
- Developer helper commands such as git summaries and project statistics
- JSON output mode for automation and agents
- Required LLM provider configuration and onboarding guide for normal agent workflows
- A default `rfs` startup flow that launches onboarding or the agent shell in interactive sessions
- Agent-guided command discovery with a defined interaction style
- Interactive shell sessions with persisted memory
- Incremental roadmap and task tracking

### Out of scope for the first release

- Full cloud sync engine
- Complex multi-user collaboration
- UI-first workflows
- Gamified TUI harbor or mini-game layers
- Broad third-party SaaS integrations beyond selected essentials
- General-purpose open-ended chat unrelated to the CLI's domain

## Success criteria

- The CLI is useful for daily local note and file retrieval
- The first search workflow can be used without manual data preparation
- Commands are scriptable and return stable JSON output
- A user can ask the CLI how to perform a task and get an actionable command back
- A user can stay inside an interactive shell session instead of retyping one-shot commands every time
- The first successful onboarding path starts with `rfs init` and a configured LLM
- The CLI remains grounded in its actual tools rather than drifting into generic assistant behavior
- The CLI agent follows one stable, documented response contract across `ask` and `shell`
- When a request is underspecified, the CLI asks one short follow-up question instead of inventing detail
- Shell guidance stays grounded in the current workspace state instead of generic advice
- The same follow-up behavior applies consistently in both `ask` and `shell`
- A user can install, verify, and recover the CLI from the documented flow without hidden steps
- A user can run one diagnostic command and see the health of config, index, shell memory, and LLM runtime
- New feature work follows documented scope, design, and roadmap updates

## Strategic principles

- Local-first before remote-first
- Reliable contracts before broad feature count
- Reusable core services before one-off commands
- Documentation before expansion
- Tool-using agent behavior over generic wrapper behavior
- Expert-reviewed multi-agent delivery to MVP before broadening scope

## Integration strategy

### Obsidian

Treat Obsidian as a first-class content source because it is local, practical, and immediately useful.

### Google Drive

Add Google Drive after the local indexing model is stable. Use it as a searchable source and metadata provider, not as the first architectural dependency.
Start with configuration, auth/cache boundaries, and a local token flow before attempting live remote search execution.

### NotebookLM

Treat NotebookLM as an adjacent workflow, not the core system of record. Design exports and source packaging that make it easier to move curated material into external research tools.

### External tool providers

Treat local companion projects such as NestClaw and qa_claw as post-MVP external tool provider candidates.
NestClaw should be approached as an API or CLI-backed service adapter, while qa_claw should be approached first as a script-runner adapter.
