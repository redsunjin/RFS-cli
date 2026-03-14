# TODO Plan

## Working rule

When scope changes, update these files in order:

1. `docs/project-charter.md`
2. `docs/product-spec.md`
3. `docs/architecture.md`
4. `docs/roadmap.md`
5. `docs/todo.md`

## Phase 0: Foundation

- [x] Choose implementation language and CLI framework
- [x] Set up repository structure
- [x] Add formatter, linter, and test runner
- [x] Create initial config file shape
- [x] Implement top-level command skeleton
- [x] Document command naming rules
- [x] Add sample fixture data for tests

## Phase 1: Local and Obsidian MVP

- [x] Define source registration model
- [x] Implement local filesystem scanner
- [x] Implement Obsidian source adapter
- [x] Support Markdown and plain text extraction
- [x] Design index record schema
- [x] Implement index persistence
- [x] Implement basic ranking strategy
- [x] Add `rfs index add`
- [x] Add `rfs index run`
- [x] Add `rfs search`
- [x] Add `rfs show`
- [x] Add result snippet generation
- [x] Add fixture-based search tests

## Phase 2: Developer utility commands

- [x] Define `dev` command contract
- [x] Implement `dev git-summary`
- [x] Implement `dev project-stats`
- [x] Implement `dev find-todo`
- [x] Add repository fixture tests where needed

## Phase 3: Agent interface hardening

- [x] Define JSON schema conventions
- [x] Add `schema_version` to machine outputs
- [x] Implement structured error model
- [x] Add `agent list-files`
- [x] Add `agent find-text`
- [x] Add contract tests for JSON output
- [x] Add output size and path-boundary safeguards
- [x] Define LLM provider config model
- [x] Add interactive `rfs llm setup`
- [x] Add `rfs llm status`
- [x] Add `rfs ask`
- [x] Add tests for configured guided-help flows
- [x] Add `rfs shell`
- [x] Persist shell memory under the workspace state directory
- [x] Allow explicit external CLI execution inside shell mode
- [x] Add `rfs init` as the required onboarding path
- [x] Add a packaged LLM onboarding guide
- [x] Apply the R2-D2-inspired agent persona to the prompt layer
- [x] Make bare `rfs` launch onboarding or shell automatically in interactive sessions
- [x] Validate `rfs ask` and `rfs shell` against a real LM Studio runtime
- [x] Strip provider-specific reasoning and control tokens from surfaced answers
- [x] Ground shell guidance in the fact that the user is already inside `rfs shell`
- [x] Define agent persona and response-style contract
- [x] Add source-aware and index-aware command suggestions to `rfs ask`
- [x] Add a short follow-up question path for ambiguous requests
- [x] Carry workspace-state grounding into natural-language guidance inside `rfs shell`
- [x] Expand shell-side ambiguous follow-up behavior to match `rfs ask`

## Phase 4: Google Drive integration

- [ ] Define Drive source config model
- [ ] Implement auth flow
- [ ] Implement file metadata retrieval
- [ ] Implement cache strategy
- [ ] Add `drive search`
- [ ] Add integration tests for adapter behavior

## Phase 5: Research workflow extensions

- [ ] Define export format for curated document bundles
- [ ] Implement research export command
- [ ] Document NotebookLM-adjacent workflow examples

## Post-MVP external tool providers

- [ ] Define a tool-provider contract for local companion projects
- [ ] Design a NestClaw adapter boundary for API or CLI invocation
- [ ] Design a qa_claw adapter boundary for script execution

## Phase 6: Release readiness

- [x] Define installation flow
- [ ] Add release versioning policy
- [ ] Add logging and diagnostics switches
- [x] Create release checklist
- [ ] Run end-to-end smoke tests
- [ ] Document the user-facing agent profile and operating boundaries

## Current recommended next three tasks

- [ ] Add release versioning policy baseline
- [ ] Add release-readiness diagnostics/logging basics
- [ ] Run an end-to-end smoke pass against the documented install flow

## MVP execution backlog

### Workstream 1: Knowledge retrieval

- [x] Improve frontmatter parser coverage
- [x] Add multi-source result ranking calibration
- [x] Add combined filter tests for source, tag, path prefix, and file type
- [x] Add richer `show` output formatting for metadata-heavy notes

### Workstream 2: Developer utilities

- [x] Define `dev` command response contract
- [x] Implement `dev find-todo`
- [x] Add tests for `dev git-summary`
- [x] Add tests for `dev project-stats`

### Workstream 3: Agent hardening

- [x] Normalize structured error codes across commands
- [x] Add JSON contract tests for `search`, `show`, `dev`, and `agent`
- [x] Add bounded output safeguards for large result sets
- [x] Add interactive LLM setup for local and compatible providers
- [x] Add command-guidance help via `rfs ask`
- [x] Add an interactive shell with persisted memory and explicit tool execution
- [x] Add required onboarding through `rfs init`
- [x] Load packaged onboarding documentation into the prompt layer
- [x] Add command suggestions that incorporate current source configuration and index availability
- [x] Define the agent persona/profile and response-style contract
- [x] Add a short follow-up question flow for ambiguous asks

### Workstream 4: MVP release prep

- [x] Add install and quickstart section to README
- [x] Add MVP smoke test checklist
- [x] Verify all documented command examples against the current CLI
- [x] Run a fixture-based smoke pass and record the QA result
- [x] Run a real-data smoke pass for the local source flow
- [x] Close the real-data Obsidian sign-off path with a documented environment-specific waiver when no real vault exists

## MVP scope review

- [x] Review remaining MVP gaps and separate post-MVP items from MVP scope
