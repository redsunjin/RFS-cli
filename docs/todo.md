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
- [ ] Implement Obsidian source adapter
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

- [ ] Define `dev` command contract
- [ ] Implement `dev git-summary`
- [ ] Implement `dev project-stats`
- [ ] Implement `dev find-todo`
- [ ] Add repository fixture tests where needed

## Phase 3: Agent interface hardening

- [ ] Define JSON schema conventions
- [ ] Add `schema_version` to machine outputs
- [ ] Implement structured error model
- [ ] Add `agent list-files`
- [ ] Add `agent find-text`
- [ ] Add contract tests for JSON output
- [ ] Add output size and path-boundary safeguards

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

- [ ] Enrich Obsidian indexing with frontmatter and note metadata
- [ ] Improve ranking and filtering beyond plain substring scoring
- [ ] Add source-aware `show` behavior and more fixture-based search coverage
