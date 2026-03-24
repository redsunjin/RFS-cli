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

Current baseline:

- Drive source config model is defined
- Drive auth flow and local token persistence are implemented
- Drive read-only metadata retrieval is implemented
- Drive local metadata cache strategy is implemented
- live cache-backed metadata search is implemented
- Drive adapter integration tests are implemented
- real Google Drive smoke is still environment-blocked until client secrets or token state exist

## Phase 5: Research workflow extensions

Goal:

Improve interoperability with external research workflows such as NotebookLM by exporting curated sources and search bundles.

Exit criteria:

- Export workflow exists for selected documents
- Research-oriented command patterns are documented

Current baseline:

- `rfs research export` now creates local bundles from indexed search results
- bundle manifests preserve source metadata, relative paths, and export locations
- the first NotebookLM-adjacent export format is documented for local handoff

## Post-MVP external tool integration track

Goal:

Define adapter boundaries for local companion projects such as NestClaw and qa_claw without expanding the MVP surface early.

Candidate milestones:

- NestClaw adapter design for API or CLI invocation
- qa_claw adapter design for script-driven workflow execution
- tool-provider registration model aligned with the existing local-first agent shell

Current baseline:

- the shared tool-provider contract is documented
- provider execution remains deferred until after the current design boundaries are reviewed

## Phase 6: Release readiness

Goal:

Prepare the project for regular personal use and future extension as a dependable CLI agent.

Exit criteria:

- Packaging and install flow are defined
- Logging and diagnostics are adequate
- Release checklist exists
- Agent interaction profile and user-facing behavior are documented

Current baseline:

- installation flow documentation is defined
- release checklist baseline is defined
- versioning policy baseline is defined
- `rfs doctor` now provides a local diagnostic and verbose inspection baseline
- install-flow smoke and user-facing agent profile are complete in the current environment

## Post-MVP gamification track

Goal:

Define an optional harbor-like TUI rest space without disturbing the core CLI agent workflow.

Candidate milestones:

- define an `rfs harbor` hub concept
- define short opt-in TUI mini-games
- keep progression and rewards isolated from core CLI state

Current slice status:

- the first `rfs harbor` concept is now documented as a separate post-MVP rest-space entrypoint
- the concept keeps harbor state optional and separate from core CLI correctness
- the first harbor progression model is now documented as a harbor-local optional layer
- the first interaction candidate is now a short `Lantern Pause` rest loop
- the first `Lantern Pause` launch decision is now plain text first, with TUI deferred
- the first incomplete-session policy is now reset-only with no resume and no reward carry-over
- incomplete first-version sessions now also avoid hidden diagnostic metrics
- the first completed-session reward is now defined as one small cosmetic unlock
- the next gamification slice is deciding whether the first completion should also grant a small point bonus

## Personal agent knowledge track

Goal:

Turn `rfs-cli` into a stronger personal agent environment by connecting roles, reusable skills, and curated knowledge notes.

Candidate milestones:

- define a shared model for agent roles, skills, and knowledge notes
- use Obsidian as a first-class storage layer for agent and skill notes
- improve retrieval of those notes through the existing indexing and search flow
- add a small read-only registry surface only after retrieval patterns are validated

Current slice status:

- the first agent-skill-knowledge operating model is now documented
- the model treats repository docs, skill assets, and Obsidian notes as separate sources of truth
- the first minimal note templates for `Agents/`, `Skills/`, and `Sources/` are now documented
- curated skill/reference note bundles should reuse the existing `rfs research export` format
- the first read-only registry surface for agent and skill notes is now documented
- the next slice is deciding whether the first CLI surface should live under `rfs agent` or remain behind existing retrieval flows longer

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

## Experimental assistive UX track

Goal:

Make `rfs-cli` easier for non-expert users by turning task-oriented requests into safe, grounded command suggestions.

Candidate milestones:

- define an internal intent model for plain-language requests
- extract a suggestion-planning module from current `ask` and `shell` flows
- align startup, `--help`, `ask`, `shell`, and recovery copy around one recommended next step
- distinguish read-only guidance from state-changing suggestions before later execution automation
- validate the experimental guidance loop without changing stable JSON contracts prematurely

Current slice status:

- branch direction for non-expert-friendly AI assistance is now documented
- first three experimental modules are defined as intent interpreter, suggestion planner, and guidance renderer
- internal `UserIntent`, `CommandSuggestion`, and `GuidanceResponse` models now exist behind the current command surface
- the first intent interpreter and suggestion-planning helpers are now extracted behind `rfs ask` and shell guidance
- progressive help now leads bare `rfs`, `rfs --help`, `rfs ask --help`, and `rfs shell --help` with one recommended next step
- text-mode recovery copy now aligns selected empty-state and setup blockers around one Korean next step
- text guidance now labels deterministic suggestions as read-only or state-changing without changing JSON contracts
- deterministic suggestions now recognize invalid index and shell-memory state and prefer `rfs doctor --verbose`
- a guidance-payload contract review now freezes the current `ask` JSON shape before any machine-readable expansion
- the current review outcome is to avoid a public guidance schema v2 in this phase and keep any future expansion as a separate proposal

## Sequencing rationale

- Phase 1 delivers the core user value soonest
- Phase 2 proves the CLI is useful outside pure search
- Phase 3 makes the tool dependable for AI integration and easier to learn at the point of use
- The agentification track builds on that foundation instead of replacing the direct-command model
- The assistive UX track builds on `ask`, `shell`, and startup behavior instead of adding a parallel command surface too early
- Phase 4 is intentionally delayed because auth and remote state add complexity
