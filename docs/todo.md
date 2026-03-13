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

## Phase 6: Release readiness

- [ ] Define installation flow
- [ ] Add release versioning policy
- [ ] Add logging and diagnostics switches
- [ ] Create release checklist
- [ ] Run end-to-end smoke tests

## Current recommended next three tasks

- [ ] Run the smoke checklist against a real Obsidian vault when one is available, or waive that step for this environment
- [ ] Validate `rfs ask` against a real Ollama or LM Studio runtime
- [ ] Design the first semantic retrieval or summarization command on top of the new LLM config layer

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
- [ ] Add command suggestions that incorporate current source configuration and index availability

### Workstream 4: MVP release prep

- [x] Add install and quickstart section to README
- [x] Add MVP smoke test checklist
- [x] Verify all documented command examples against the current CLI
- [x] Run a fixture-based smoke pass and record the QA result
- [x] Run a real-data smoke pass for the local source flow
- [ ] Run a real-data smoke pass for the Obsidian source flow

## MVP scope review

- [x] Review remaining MVP gaps and separate post-MVP items from MVP scope
