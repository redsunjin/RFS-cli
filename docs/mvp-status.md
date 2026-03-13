# MVP Status

## Current MVP status

The project is in final MVP sign-off.

## Completed MVP areas

- Local and Obsidian source registration
- Local JSON index persistence
- Indexed search with source, source-id, tag, path prefix, and file type filters
- Indexed document inspection with source metadata
- Baseline developer utilities: `git-summary`, `project-stats`, `find-todo`
- Agent-safe commands with structured JSON output
- Structured error payloads for common failure cases
- Quickstart and smoke checklist documentation
- Fixture-backed verification of documented command flows
- Real-data smoke verification for the local source flow

## Remaining MVP areas

- Run the smoke checklist against a real Obsidian vault path, if one is available in the target environment
- Decide whether that Obsidian-specific real-data step is required for MVP sign-off in environments where no vault exists yet

## Post-MVP areas

- Google Drive integration
- NotebookLM-adjacent export workflows
- Broader document extraction beyond current text-centric support
- Background sync or watch mode
- Packaging and release automation

## Current recommendation

Treat the core CLI as MVP-ready except for the environment-specific Obsidian sign-off step. New feature work should stay behind explicit post-MVP planning unless it directly improves release confidence.
