# Harbor Diagnostic Metrics Policy

## Goal

Define whether incomplete first-version `Lantern Pause` sessions should appear in any hidden diagnostic metric.

## First-version decision

For the first runtime version, incomplete harbor sessions should not be counted in any hidden diagnostic metric.

That means:

- no abandoned-session counter
- no hidden retry counter
- no internal failure ratio derived from normal early exits
- no diagnostic summary surfaced to the user for ordinary incomplete sessions

## Why this is the right first step

- the first harbor launch should stay simple
- normal early exits are expected and should not feel like failures
- hidden counters add state complexity before the interaction is validated
- there is no operational need yet for a diagnostic signal from an optional rest loop

## Scope boundary

This decision applies only to ordinary incomplete `Lantern Pause` sessions in the first version.

It does not prevent later technical logging for:

- actual runtime crashes
- explicit debug builds
- developer-only troubleshooting during implementation

But those cases should remain outside the user-facing progression model and outside ordinary harbor flow.

## User-facing rule

The user experience should remain simple:

- finish the session to receive completion credit
- leave early and nothing is recorded
- come back later and start fresh

No hidden abandoned-session tracking should influence progression or future prompts.

## Non-goals

This policy does not include:

- analytics dashboards
- abandonment scoring
- behavior-shaping nudges based on early exits
- links to core CLI diagnostics such as `rfs doctor`

## Acceptance criteria

Before implementation starts, this policy should satisfy all of these:

1. Normal incomplete sessions do not create hidden diagnostic counters.
2. Early exits do not change progression or future harbor behavior.
3. The first runtime remains explainable without invisible state.
4. The decision does not affect behavior outside `rfs harbor`.

## Recommended next slices

1. Define the minimal cosmetic unlock rule for the first completed sessions.
2. Decide whether the first completion reward should be purely cosmetic or include a small point bonus as well.
3. If runtime implementation begins, keep crash-only debug logging separate from harbor progression state.
