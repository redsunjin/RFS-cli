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

- [x] Define Drive source config model
- [x] Implement auth flow
- [x] Implement file metadata retrieval
- [x] Implement cache strategy
- [x] Add `drive search`
- [x] Add integration tests for adapter behavior

## Phase 5: Research workflow extensions

- [x] Define export format for curated document bundles
- [x] Implement research export command
- [x] Document NotebookLM-adjacent workflow examples

## Post-MVP external tool providers

- [x] Define a tool-provider contract for local companion projects
- [x] Design a NestClaw adapter boundary for API or CLI invocation
- [x] Design a qa_claw adapter boundary for script execution

## Phase 6: Release readiness

- [x] Define installation flow
- [x] Add release versioning policy
- [x] Add logging and diagnostics switches
- [x] Create release checklist
- [x] Run end-to-end smoke tests
- [x] Document the user-facing agent profile and operating boundaries

## Current recommended next three tasks

- [ ] Run a real Google Drive smoke pass when client secrets or token state are available
- [ ] Record a real Google Drive smoke result in the QA report once credentials are available
- [ ] Keep any future guidance-payload expansion behind a dedicated contract review note written from the shared template

## Current work groups

- [ ] `WG-01` Google Drive runtime validation
- [x] `WG-02` Research export polish
- [x] `WG-03` Assistive UX batch A
- [x] `WG-04` External tool provider design
- [x] `WG-05` Harbor and game planning
- [x] `WG-06` Recovery-first UX copy
- [x] `WG-07` Assistive UX batch B
- [x] `WG-08` Assistive UX batch C

See `docs/work-groups.md` for batch contents, blockers, and review order.

## Idea branch recommended next three tasks

- [ ] Record any future guidance-payload expansion in a dedicated contract review note first
- [ ] Reopen the contract only if an unattended-execution use case is actually approved
- [x] Continue human-facing help polish without exposing startup or shell help as public API

## Idea branch: Assistive UX experiments

- [x] Create internal guidance modules instead of adding a new top-level command surface
- [x] Define intent categories such as setup, add-source, search, inspect, and diagnose
- [x] Ground command suggestions in config, index, shell-memory, and doctor-visible state
- [x] Add progressive help rendering for bare `rfs`, `--help`, `ask`, and `shell`
- [x] Explain empty states and missing setup in plain Korean with one recommended next step
- [x] Distinguish read-only suggestions from state-changing suggestions before execution automation
- [x] Add contract review before exposing any machine-readable guidance payload
- [x] Keep grounded startup and shell help examples aligned with implemented source-listing and recent-command recall
- [x] Add a shared template for future guidance contract review notes

## Idea branch recommended next three tasks

- [x] Define `UserIntent`, `CommandSuggestion`, and `GuidanceResponse` internal models
- [x] Extract an intent interpreter and suggestion planner behind `rfs ask`
- [x] Add tests for plain-language command suggestion and short follow-up behavior

## Idea branch: Assistive UX experiments

- [x] Create internal guidance modules instead of adding a new top-level command surface
- [x] Define intent categories such as setup, add-source, search, inspect, and diagnose
- [x] Ground command suggestions in config, index, shell-memory, and doctor-visible state
- [x] Add progressive help rendering for bare `rfs`, `--help`, `ask`, and `shell`
- [x] Explain empty states and missing setup in plain Korean with one recommended next step
- [x] Distinguish read-only suggestions from state-changing suggestions before execution automation
- [x] Add contract review before exposing any machine-readable guidance payload

## Post-MVP gamification track

- [x] Define an optional `rfs harbor` rest-space concept
- [x] Design a small reward/progression model that stays outside core CLI state
- [x] Design one or two short TUI mini-games for optional use

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
