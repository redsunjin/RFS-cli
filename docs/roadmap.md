# Roadmap

## Phase 0: Foundation

Goal:

Set up the repository, toolchain, baseline command structure, and documentation-driven workflow.

Exit criteria:

- Project scaffolding exists
- Documentation set is committed
- Basic CLI command skeleton runs

## Phase 1: Local and Obsidian MVP

Goal:

Deliver useful local indexing and search for Markdown and text files, with Obsidian as a first-class source.

Exit criteria:

- Source roots can be configured
- Local index can be created and refreshed
- Search returns ranked results
- `show` displays result details

### MVP sub-goals inside Phase 1

- frontmatter and note metadata are indexed for Obsidian notes
- search supports practical filters and stable ranking
- indexed inspection output is useful for daily note retrieval

## Phase 2: Developer utility commands

Goal:

Add commands that improve day-to-day development workflows and validate the multi-domain command structure.

Exit criteria:

- `dev git-summary` works
- `dev project-stats` works
- At least one codebase scanning command exists

## Phase 3: Agent interface hardening

Goal:

Make the CLI reliable for machine usage with stable JSON schemas, bounded output, clear error behavior, guided command discovery, and the first layer of coherent agent behavior.

Exit criteria:

- JSON output contracts are documented
- Agent-safe commands exist
- Contract tests cover machine-readable responses
- Required LLM provider setup exists for guided command usage
- A conversational help path exists without becoming a hard dependency for core commands
- Conversational answers stay grounded in supported commands and product scope
- An interactive shell exists for multi-turn local operation with persisted session memory
- A required onboarding path exists through `rfs init` and the packaged LLM onboarding guide
- Interactive startup through bare `rfs` launches onboarding or shell without extra command discovery

## MVP target

The first MVP spans:

- Phase 1 complete
- Phase 2 complete
- a limited but reliable subset of Phase 3

That means the project should not wait for Google Drive integration before declaring an MVP.

## Phase 4: Google Drive integration

Goal:

Introduce remote file discovery and search without destabilizing the local-first architecture.

Exit criteria:

- Drive auth and configuration are supported
- Drive metadata can be searched
- Cache or sync behavior is documented and tested

## Phase 5: Research workflow extensions

Goal:

Improve interoperability with external research workflows such as NotebookLM by exporting curated sources and search bundles.

Exit criteria:

- Export workflow exists for selected documents
- Research-oriented command patterns are documented

## Post-MVP external tool integration track

Goal:

Define adapter boundaries for local companion projects such as NestClaw and qa_claw without expanding the MVP surface early.

Candidate milestones:

- NestClaw adapter design for API or CLI invocation
- qa_claw adapter design for script-driven workflow execution
- tool-provider registration model aligned with the existing local-first agent shell

## Phase 6: Release readiness

Goal:

Prepare the project for regular personal use and future extension as a dependable CLI agent.

Exit criteria:

- Packaging and install flow are defined
- Logging and diagnostics are adequate
- Release checklist exists
- Agent interaction profile and user-facing behavior are documented

## Agentification track

After the current MVP hardening work, the next product-shaping track is turning `rfs-cli` into a stronger CLI-native agent.

Candidate milestones:

- source-aware and index-aware command suggestions
- short follow-up questions for ambiguous requests
- a documented agent profile with stable tone and operating boundaries
- interactive shell memory that feeds better follow-up guidance
- tighter onboarding and persona alignment between docs and runtime prompts

Current status:

- persona and response-style contract documentation is complete
- `rfs ask` now has a baseline of source-aware and index-aware grounding
- `rfs ask` now has a deterministic short follow-up path for ambiguous requests
- natural-language guidance inside `rfs shell` now carries workspace-state grounding
- natural-language guidance inside `rfs shell` now mirrors the same short follow-up behavior
- the current implementation is ready to move from agent hardening into release-readiness work

## Sequencing rationale

- Phase 1 delivers the core user value soonest
- Phase 2 proves the CLI is useful outside pure search
- Phase 3 makes the tool dependable for AI integration and easier to learn at the point of use
- The agentification track builds on that foundation instead of replacing the direct-command model
- Phase 4 is intentionally delayed because auth and remote state add complexity
