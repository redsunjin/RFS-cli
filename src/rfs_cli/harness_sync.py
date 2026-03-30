from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import List

HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$")
NUMBERED_ITEM_PATTERN = re.compile(r"^\d+\.\s+(.*)$")
CHECKBOX_ITEM_PATTERN = re.compile(r"^- \[(?P<done>[ xX])\]\s+(.*)$")
NEXT_SLICE_PATTERN = re.compile(r"^- the next .* slice is (.+)$", re.IGNORECASE)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section_lines(text: str, heading: str) -> List[str]:
    lines = text.splitlines()
    capture = False
    collected: List[str] = []
    target = heading.strip().lower()

    for line in lines:
        match = HEADING_PATTERN.match(line.strip())
        if match:
            current = match.group(1).strip().lower()
            if capture:
                break
            if current == target:
                capture = True
            continue
        if capture:
            collected.append(line.rstrip())

    return collected


def parse_numbered_items(lines: List[str]) -> List[str]:
    items: List[str] = []
    for line in lines:
        match = NUMBERED_ITEM_PATTERN.match(line.strip())
        if match:
            items.append(match.group(1).strip())
    return items


def parse_checkbox_items(lines: List[str], checked: bool | None = None) -> List[str]:
    items: List[str] = []
    for line in lines:
        match = CHECKBOX_ITEM_PATTERN.match(line.strip())
        if not match:
            continue
        is_checked = match.group("done").lower() == "x"
        if checked is not None and is_checked != checked:
            continue
        items.append(match.group(2).strip())
    return items


def normalize_text(value: str) -> str:
    lowered = value.lower().replace("`", " ")
    tokens = re.findall(r"[a-z0-9]+", lowered)
    normalized_tokens = []
    for token in tokens:
        if token.endswith("ing") and len(token) > 5:
            token = token[:-3]
        elif token.endswith("ed") and len(token) > 4:
            token = token[:-2]
        elif token.endswith("s") and len(token) > 4:
            token = token[:-1]
        normalized_tokens.append(token)
    return " ".join(normalized_tokens)


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()


def official_active_loop_tasks_from_roadmap(text: str) -> List[str]:
    return parse_numbered_items(section_lines(text, "Current official active loop"))


def official_active_loop_tasks_from_todo(text: str) -> List[str]:
    return parse_checkbox_items(
        section_lines(text, "Current recommended next three tasks"),
        checked=False,
    )


def roadmap_track_next_slices(text: str) -> List[str]:
    matches: List[str] = []
    for line in text.splitlines():
        match = NEXT_SLICE_PATTERN.match(line.strip())
        if match:
            matches.append(match.group(1).strip())
    return matches


def open_todo_items(text: str) -> List[str]:
    return parse_checkbox_items(text.splitlines(), checked=False)


def find_sync_errors(roadmap_text: str, todo_text: str) -> List[str]:
    errors: List[str] = []

    roadmap_tasks = official_active_loop_tasks_from_roadmap(roadmap_text)
    todo_tasks = official_active_loop_tasks_from_todo(todo_text)

    if len(roadmap_tasks) != len(todo_tasks):
        errors.append(
            "Current official active loop tasks differ between docs/roadmap.md and docs/todo.md."
        )
    else:
        for roadmap_task, todo_task in zip(roadmap_tasks, todo_tasks):
            if similarity(roadmap_task, todo_task) < 0.7:
                errors.append(
                    "Current official active loop tasks differ between docs/roadmap.md and "
                    "docs/todo.md."
                )
                break

    open_items = open_todo_items(todo_text)
    for next_slice in roadmap_track_next_slices(roadmap_text):
        best_score = max((similarity(next_slice, item) for item in open_items), default=0.0)
        if best_score < 0.55:
            errors.append(
                "Roadmap next-slice note has no matching open TODO item: "
                f"'{next_slice}'."
            )

    return errors
