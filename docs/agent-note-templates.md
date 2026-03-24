# Agent Note Templates

## Goal

Define the smallest useful note templates for the first `Agents/`, `Skills/`, and `Sources/` note sets in Obsidian.

These templates are meant to keep note capture consistent enough for retrieval while staying lightweight enough to use daily.

## Template principles

- keep fields short and human-editable
- prefer one note per role, skill, or source
- make notes useful in plain Markdown before any registry feature exists
- keep project-critical behavior in repository docs, not only in notes

## `Agents/` template

Use one note per stable role or operating persona.

Suggested structure:

```md
# <Agent Name>

## Purpose
- What this role is for

## Responsibilities
- What this role should evaluate or decide

## Inputs
- What documents, state, or signals this role should look at

## Outputs
- What kind of recommendation, review, or artifact this role should produce

## Heuristics
- Short rules of thumb

## Boundaries
- What this role should not decide or override

## Related Skills
- Links to reusable skill notes

## References
- Links to relevant project docs or external notes
```

Minimum retrieval fields:

- `Purpose`
- `Responsibilities`
- `Boundaries`
- `Related Skills`

## `Skills/` template

Use one note per reusable workflow, checklist, or command pattern.

Suggested structure:

```md
# <Skill Name>

## Purpose
- What recurring task this skill helps with

## Trigger
- When to use it

## Inputs
- What the skill needs before it starts

## Steps
1. Minimal ordered workflow

## Outputs
- What artifact, decision, or result should come out

## Constraints
- Safety rules, scope limits, or non-goals

## Example
- One short example or command

## Related Agents
- Links to role notes that commonly use this skill

## References
- Links to docs, experiments, or external sources
```

Minimum retrieval fields:

- `Purpose`
- `Trigger`
- `Steps`
- `Constraints`

## `Sources/` template

Use one note per external project, article, repo, conversation set, or research source.

Suggested structure:

```md
# <Source Name>

## What It Is
- Short description of the source

## Why It Matters
- Why it is relevant to `rfs-cli`

## Reusable Ideas
- Specific ideas worth borrowing

## Things To Avoid
- Patterns that do not fit this project

## Related Skills
- Links to skill notes influenced by this source

## Related Experiments
- Links to local experiments or decisions

## Links
- Canonical URLs or repo links
```

Minimum retrieval fields:

- `What It Is`
- `Why It Matters`
- `Reusable Ideas`
- `Things To Avoid`

## Tagging guidance

Keep tags lightweight.
The first useful tags are:

- `agent-role`
- `skill`
- `source-note`
- `pattern`
- `experiment`

Optional topical tags may include:

- `review`
- `qa`
- `architecture`
- `obsidian`
- `prompting`
- `research`

## Naming guidance

- `Agents/`: use stable role names such as `Product and Roadmap`
- `Skills/`: use action-oriented names such as `Contract Hardening Review`
- `Sources/`: use canonical source names such as `gstack` or `oh-my-openagent`

Avoid vague names like `ideas`, `misc`, or `agent stuff`.

## Retrieval guidance

The first retrieval pass should work well even if only headings and short bullets are indexed.

That means notes should:

- place the purpose near the top
- keep boundaries explicit
- include a few concrete nouns users would actually search
- link related notes directly when useful

## Non-goals

These templates do not require:

- YAML frontmatter
- a fixed machine schema
- automatic registry sync
- execution metadata
- multi-user governance

## Recommended next slices

1. Decide whether `Sources/` notes need a lightweight comparison section for competing ideas.
2. Decide whether `Skills/` notes should include one command block by default.
3. If registry work begins later, define a read-only extracted field set rather than changing the note-writing style first.
