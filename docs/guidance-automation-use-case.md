# Guidance Automation Use Case

## Date

2026-03-17

## Purpose

Validate the current public guidance contract against one concrete automation scenario before adding new machine-readable fields.

## Chosen scenario

Human-in-the-loop workspace assistant.

Example flow:

1. an automation or local agent asks `rfs ask "<task>" --format json`
2. it reads the response and decides whether the user can be shown one next action immediately
3. if the request is underspecified, it shows the follow-up question instead of guessing
4. if the request is state-changing, it keeps the user in the approval loop

## Example request

```bash
rfs ask "Obsidian 볼트를 추가하고 검색을 시작하려면?" --format json
```

## Fields the automation needs

- `answer`
  - user-facing summary for the inbox or assistant view
- `follow_up_required`
  - decide whether the workflow can continue or must ask the user one more thing
- `follow_up_question`
  - exact next prompt when the request is underspecified
- `action_type`
  - decide whether the recommendation is read-only or state-changing

## Why the current contract is sufficient

For a human-in-the-loop automation, the workflow goal is not autonomous execution.
It is safe next-step guidance with clear escalation when input is missing.

That means the automation does not need:

- startup help block structure
- shell `/help` block structure
- raw internal intent labels
- deterministic ranking internals
- hidden planning state

The current public `ask` payload already lets the automation decide:

- show the answer now
- ask one follow-up question
- hold for approval if the step changes state

## Why new fields are not added now

Candidate fields such as `recommended_command`, `confidence`, `entities`, or `intent_goal` would make the contract wider.
That wider contract would only be justified if `rfs` were expected to drive unattended command execution.

That is not the approved product boundary today.
The current boundary is guidance-first, human-reviewed operation.

## Result of the validation

- the current `ask` JSON contract is sufficient for a human-in-the-loop automation
- startup and shell help should remain human-facing text surfaces
- internal guidance models should remain internal
- no new machine-readable guidance field is justified by this scenario

## Future trigger for revisiting this decision

Reopen the contract only if one of these becomes a real requirement:

- approved unattended execution of suggested commands
- multi-step automation planning that cannot rely on the current `answer` plus follow-up flow
- a reviewed external tool-provider workflow that needs a stable structured command field
