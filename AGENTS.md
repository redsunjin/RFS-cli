# AGENTS.md

This repository uses a documentation-first workflow. Agents should keep the project charter, spec, architecture, roadmap, and TODO plan aligned before expanding scope.

## Agent group

Use the following specialist roles when planning or implementing work:

### 1. Product and roadmap agent

Responsibilities:

- maintain project intent
- decide priorities and scope boundaries
- keep roadmap and TODOs in sync

Primary outputs:

- charter updates
- roadmap updates
- milestone decisions

### 2. CLI architect agent

Responsibilities:

- define command structure
- maintain module boundaries
- keep configuration and output contracts coherent

Primary outputs:

- command model decisions
- architecture updates
- technical design notes

### 3. Knowledge integration agent

Responsibilities:

- design and implement content source adapters
- model Obsidian and local filesystem ingestion
- later handle Google Drive integration

Primary outputs:

- source adapter specs
- indexing rules
- extraction behavior decisions

### 4. Search and retrieval agent

Responsibilities:

- design indexing model
- implement query behavior and ranking
- improve snippets, filters, and recall

Primary outputs:

- search behavior definitions
- ranking decisions
- retrieval test cases

### 5. AI tooling agent

Responsibilities:

- define machine-readable contracts
- harden commands for safe agent execution
- keep JSON output stable and documented

Primary outputs:

- schema definitions
- error contract decisions
- agent command guidelines

### 6. QA and release agent

Responsibilities:

- define test coverage expectations
- verify behavior across commands
- maintain release readiness checklists

Primary outputs:

- test plans
- validation reports
- release checklists

## Recommended operating order

For non-trivial work, use this sequence:

1. Product and roadmap agent clarifies the change
2. CLI architect agent updates the design if needed
3. Specialist implementation agent executes the feature
4. AI tooling agent reviews command contracts if output changes
5. QA and release agent validates the result

## MVP delivery mode

When the project is in active MVP delivery, agents should work in short loops with explicit review gates.

### Delivery loop

1. Product and roadmap agent selects one MVP-sized slice from `docs/mvp-plan.md` or `docs/todo.md`
2. CLI architect agent confirms command shape, module boundaries, and document impact
3. Primary implementation agent executes the slice
4. Relevant specialist agent reviews the implementation against its domain
5. AI tooling agent reviews output contracts if CLI behavior or payloads changed
6. QA and release agent runs validation, records gaps, and blocks completion if criteria fail

### Slice size rule

- One slice should be small enough to complete with code, tests, and docs in one cycle
- If a slice spans more than one workstream, split it before implementation

## Review responsibilities by agent

### Product and roadmap agent

- checks scope creep
- checks whether the slice still belongs to MVP
- checks whether TODO and roadmap updates are needed

### CLI architect agent

- checks command naming
- checks module boundaries
- checks whether adapters and output models stay coherent

### Knowledge integration agent

- checks source handling
- checks metadata extraction quality
- checks source-specific edge cases such as Obsidian vault behavior

### Search and retrieval agent

- checks ranking logic
- checks filter semantics
- checks snippet and recall behavior

### AI tooling agent

- checks JSON schema stability
- checks error model consistency
- checks command safety and bounded output expectations

### QA and release agent

- checks tests and linters
- checks regression risk
- checks whether acceptance criteria are actually satisfied

## Required handoff artifacts

Each completed slice should leave behind:

- updated docs if behavior or scope changed
- tests for the new or changed behavior
- a brief validation result
- a clear next slice recommendation

## Blockers

Do not mark a slice complete if any of the following are true:

- docs and implementation disagree
- tests are missing for changed behavior
- a command contract changed without AI tooling review
- the slice added scope that belongs to a later phase

## Documentation rules

When a feature changes scope or behavior, update documents in this order:

1. `docs/project-charter.md`
2. `docs/product-spec.md`
3. `docs/architecture.md`
4. `docs/roadmap.md`
5. `docs/todo.md`

## Attachment handling rules

- Before planning or implementation, read all relevant repository documents and any attached development materials that affect requirements, architecture, workflows, or acceptance criteria.
- Prioritize attachments that contain specs, notes, diagrams, screenshots, logs, API details, or task breakdowns.
- If an attachment changes a durable project decision, copy the distilled decision into the repository documents listed above.
- Do not leave critical requirements only inside transient attachments; promote them into repo docs during the same work cycle.

## Working rules

- Prefer small increments that preserve a usable CLI state
- Keep command names stable once documented
- Do not introduce remote integrations before the local-first model is working
- Treat AI-safe JSON output as a product feature, not an afterthought
- Add or update tests for behavior changes

## Current recommendation

For the next implementation cycle, actively emphasize these agents:

- Product and roadmap agent
- CLI architect agent
- Knowledge integration agent
- AI tooling agent

This combination fits the current stage, where the project still needs scope control, command design, indexing design, and machine-readable tool contracts.
