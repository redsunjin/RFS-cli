from pathlib import Path

from rfs_cli.harness_sync import find_sync_errors


def test_repo_docs_harness_sync_passes() -> None:
    roadmap_text = Path("docs/roadmap.md").read_text(encoding="utf-8")
    todo_text = Path("docs/todo.md").read_text(encoding="utf-8")

    assert find_sync_errors(roadmap_text, todo_text) == []


def test_find_sync_errors_reports_missing_matching_todo_item() -> None:
    roadmap_text = "\n".join(
        [
            "## Current official active loop",
            "",
            "1. Run Drive smoke",
            "",
            "## Track",
            "",
            "- the next registry slice is deciding whether the registry should stay index-backed",
        ]
    )
    todo_text = "\n".join(
        [
            "## Current recommended next three tasks",
            "",
            "- [ ] Run Drive smoke",
            "",
            "## Personal track",
            "",
            "- [ ] Design a different adapter boundary",
        ]
    )

    errors = find_sync_errors(roadmap_text, todo_text)

    assert errors == [
        "Roadmap next-slice note has no matching open TODO item: "
        "'deciding whether the registry should stay index-backed'."
    ]
