# MVP Status

## Date

2026-03-14

## Current status

The project is signed off as MVP-ready for the local-first CLI agent baseline in the current environment.

The core command surface, LLM-backed onboarding, interactive shell flow, real local-data validation, and real LM Studio runtime validation are all in place.
The Obsidian real-data smoke step is waived for this environment because no real vault path is currently available.

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
- Sanitized LM Studio/Qwen output that strips reasoning tags and control markers
- Shell-session grounding so in-shell guidance knows the user is already inside `rfs shell`
- Quickstart and smoke checklist documentation
- Fixture-backed verification of documented command flows
- Real-data smoke verification for the local source flow
- Real LM Studio runtime verification for `llm status`, `ask`, and `shell`

## Validation baseline

- `uv run pytest`: pass
- `uv run ruff check .`: pass
- fixture-based smoke: pass
- real local-data smoke: pass
- real LM Studio runtime validation: pass

## MVP sign-off note

The only previously open sign-off item was a real Obsidian vault smoke pass.
That step is now explicitly waived for this environment because no real vault path is available on the machine.
If a real vault path appears later, run the smoke checklist as an additional confidence check rather than as an MVP blocker.

## Immediate next build focus

The release-readiness baseline is now complete in the current environment.
The next work should move into post-MVP expansion rather than further release-baseline hardening.

Priority order:

1. Google Drive source model and auth boundary
2. Google Drive metadata retrieval and cache design
3. post-MVP companion integrations and optional gamification planning

## Post-MVP areas

- Google Drive integration
- NotebookLM-adjacent export workflows
- External tool providers such as NestClaw and qa_claw
- Broader document extraction beyond current text-centric support
- Background sync or watch mode
- Packaging and release automation

## Recommendation

Treat the MVP as signed off for the current environment.
The next work should stay focused on agent guidance quality and release readiness, not on broadening the integration surface.
