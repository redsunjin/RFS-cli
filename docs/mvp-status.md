# MVP Status

## Date

2026-03-13

## Current status

The project is functionally MVP-ready for the local-first CLI agent baseline.

The core command surface, LLM-backed onboarding, interactive shell flow, and real local-data validation are all in place.
The only remaining environment-specific MVP sign-off item is a real Obsidian vault smoke run, or an explicit decision to waive that step in environments where no vault exists.

## Completed areas

- Local and Obsidian source registration
- Local JSON index persistence
- Indexed search with source, source-id, tag, path prefix, and file type filters
- Indexed document inspection with source metadata
- Baseline developer utilities: `git-summary`, `project-stats`, `find-todo`
- Agent-safe commands with structured JSON output
- Structured error payloads for common failure cases
- Required LLM onboarding through `rfs init`
- Packaged LLM onboarding guide loaded into the runtime prompt
- R2-D2-inspired CLI agent persona baseline
- Interactive shell with persisted session memory
- Bare `rfs` interactive startup that launches onboarding or shell automatically
- Graceful shell handling when the configured LLM times out
- Quickstart and smoke checklist documentation
- Fixture-backed verification of documented command flows
- Real-data smoke verification for the local source flow

## Validation baseline

- `uv run pytest`: pass
- `uv run ruff check .`: pass
- fixture-based smoke: pass
- real local-data smoke: pass

## Remaining MVP sign-off items

- Run the smoke checklist against a real Obsidian vault path, if one is available in the target environment
- Decide whether that Obsidian-specific real-data step is required for MVP sign-off in environments where no vault exists yet

## Immediate next build focus

After MVP sign-off, the next product-shaping work should stay inside agent hardening rather than expanding integrations.

Priority order:

1. define the agent persona and response-style contract
2. add source-aware and index-aware command suggestions to `rfs ask`
3. add a short follow-up question path for ambiguous requests
4. validate `rfs ask` and `rfs shell` against a real LM Studio or Ollama runtime
5. prepare release-readiness basics such as installation flow and release checklist

## Post-MVP areas

- Google Drive integration
- NotebookLM-adjacent export workflows
- External tool providers such as NestClaw and qa_claw
- Broader document extraction beyond current text-centric support
- Background sync or watch mode
- Packaging and release automation

## Recommendation

Treat the current codebase as ready for MVP sign-off once the Obsidian real-data question is closed.
Until then, new work should focus on release confidence and agent guidance quality, not on broadening the integration surface.
