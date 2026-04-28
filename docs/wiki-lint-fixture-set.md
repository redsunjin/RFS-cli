# Wiki Lint Fixture Set

## Goal

Define the first small fixture set for `rfs wiki lint` before runtime implementation starts.

The fixture set is intentionally structural.
It gives the first runtime version a bounded target without forcing semantic contradiction or staleness logic too early.

## Fixture root

The first fixture trees live under:

- `tests/fixtures/wiki_lint/`

Each fixture uses the documented knowledge-root shape:

```text
<fixture>/
  raw/
  wiki/
    index.md
    log.md
    overview.md
    concepts/
    entities/
    questions/
```

Not every fixture needs every optional subdirectory, but every valid fixture should respect the `wiki/` content boundary and required files.

## First fixture cases

### 1. `healthy_minimal`

Purpose:

- represents a small valid wiki tree
- should produce zero issues in the first runtime version

Coverage:

- required files exist
- page links resolve
- maintained pages are reachable from `index.md`

### 2. `missing_page`

Purpose:

- exercises `missing_page`

Coverage:

- one page links to a missing wiki page
- lint should surface the missing target path

### 3. `orphan_page`

Purpose:

- exercises `orphan_page`

Coverage:

- one maintained page exists under `wiki/concepts/` but is not linked from `index.md`, `overview.md`, or any other page

### 4. `missing_crosslink`

Purpose:

- exercises `missing_crosslink`

Coverage:

- a maintained page is reachable from `index.md` but has no outbound wiki link to any related page in a multi-page wiki tree

### 5. `invalid_state_missing_log`

Purpose:

- exercises `invalid_wiki_state`

Coverage:

- the wiki tree is present but one required file is missing
- the first runtime should fail rather than emit a normal lint report

## First-version category mapping

The first fixture set intentionally focuses on:

- `missing_page`
- `orphan_page`
- `missing_crosslink`
- `invalid_wiki_state`

The report contract still reserves:

- `contradiction`
- `stale_claim`
- `coverage_gap`

But those categories may remain zero-count in the first runtime implementation until a stronger heuristic is accepted.

## Naming rule

Fixture names should describe the primary expected outcome, not the future implementation detail.

Examples:

- `healthy_minimal`
- `missing_page`
- `orphan_page`
- `missing_crosslink`
- `invalid_state_missing_log`

## Recommended next slice

1. implement the first `rfs wiki lint` runtime against this fixture set
2. keep the first runtime structural and read-only
3. defer contradiction and stale-claim heuristics until the structural lint pass is accepted
