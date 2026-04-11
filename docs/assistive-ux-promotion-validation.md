# Assistive UX Promotion Validation

Date: 2026-04-10

## Scope

Validate the assistive UX slice before closing its promotion into the official loop.

This slice covers:

- progressive help for `rfs`, `--help`, `ask`, and `shell`
- recovery-oriented Korean guidance for selected setup and empty-state blockers
- deterministic read-only versus state-changing guidance labels
- the decision to keep the current `ask` JSON contract frozen without a public guidance schema v2

## Decision summary

- The validated assistive UX behavior is now promoted into the official loop.
- The current `ask` JSON contract remains frozen for this phase.
- Human-facing guidance may continue to improve, but machine-readable guidance does not widen in this slice.

## Validation run

Commands run:

- `uv run rfs --help`
- `uv run pytest tests/test_cli.py -q -k "ask_json_contract or render_guidance_response or shell_returns or ask_text_returns or deterministic"`
- `python3 scripts/check_harness_sync.py`
- `uv run pytest tests/test_harness_sync.py -q`

Results:

- CLI entrypoint: pass
- assistive UX focused CLI tests: pass
- harness sync: pass
- harness sync pytest coverage: pass

## What this proves

- `rfs-cli` is runnable now through the packaged script entrypoint
- the current startup and help surface already reflects the promoted assistive UX behavior
- deterministic guidance continues to distinguish read-only and state-changing suggestions
- the current JSON guidance contract remains narrow and stable

## Residual risks

- this slice validates the guided-help surface and its focused tests, not a broader real-user UX study
- the guidance module split is still not fully extracted out of all runtime code paths
- broader machine-readable guidance expansion remains deferred by design

## Next slice recommendation

The official loop should now move to re-ranking the paused post-MVP queue and selecting one bounded next slice.

Recommend this order:

1. select the next official slice from the paused queue
2. keep compiled wiki work as candidate-track incubation
3. return to implementation only after the next official slice is fixed in roadmap and TODO
