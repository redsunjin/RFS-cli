# Project Charter

## Mission

Build a personal CLI that unifies knowledge retrieval, developer utilities, and AI-tool execution into one consistent interface.

## Why this project exists

The project is primarily a learning vehicle, but it must also become a real tool that is useful in daily work. The CLI should reduce friction when searching notes, inspecting files, summarizing project state, and providing reliable tool output for AI agents.

## Primary outcomes

- Make personal knowledge easy to search across Obsidian and local documents
- Provide a practical CLI foundation for future integrations such as Google Drive
- Create AI-safe command contracts with deterministic JSON output
- Establish a documentation-driven development process from the beginning

## Problem statement

Personal knowledge and project context are fragmented across multiple systems:

- Obsidian vaults
- Local folders
- Google Drive
- External research workflows such as NotebookLM

The current friction is not only data access, but also the lack of one stable interface that both a human and an AI tool can use consistently.

## Product vision

`rfs-cli` becomes a local command center for:

- knowledge discovery
- file inspection
- developer workflow support
- agent tool execution

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
- Incremental roadmap and task tracking

### Out of scope for the first release

- Full cloud sync engine
- Complex multi-user collaboration
- UI-first workflows
- Broad third-party SaaS integrations beyond selected essentials

## Success criteria

- The CLI is useful for daily local note and file retrieval
- The first search workflow can be used without manual data preparation
- Commands are scriptable and return stable JSON output
- New feature work follows documented scope, design, and roadmap updates

## Strategic principles

- Local-first before remote-first
- Reliable contracts before broad feature count
- Reusable core services before one-off commands
- Documentation before expansion
- Expert-reviewed multi-agent delivery to MVP before broadening scope

## Integration strategy

### Obsidian

Treat Obsidian as a first-class content source because it is local, practical, and immediately useful.

### Google Drive

Add Google Drive after the local indexing model is stable. Use it as a searchable source and metadata provider, not as the first architectural dependency.

### NotebookLM

Treat NotebookLM as an adjacent workflow, not the core system of record. Design exports and source packaging that make it easier to move curated material into external research tools.
