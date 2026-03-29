from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Dict, List, Literal, Optional

from rfs_cli.models import IndexDocument, IndexStore

NoteKind = Literal["role", "skill"]

SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$")
WIKI_LINK_PATTERN = re.compile(r"^\[\[([^\]]+)\]\]$")
MARKDOWN_LINK_PATTERN = re.compile(r"^\[([^\]]+)\]\([^)]+\)$")
NOTE_FOLDER_BY_KIND: dict[NoteKind, str] = {
    "role": "agents",
    "skill": "skills",
}


def list_note_records(
    index_store: IndexStore,
    kind: NoteKind,
    limit: int = 50,
) -> List[dict[str, object]]:
    records: List[dict[str, object]] = []

    for document in index_store.documents:
        if classify_note_document(document) != kind:
            continue
        records.append(build_note_record(document, kind))

    records.sort(key=lambda item: str(item["name"]).lower())
    return records[:limit]


def get_note_record(index_store: IndexStore, document_id: str) -> Optional[dict[str, object]]:
    for document in index_store.documents:
        kind = classify_note_document(document)
        if kind is None:
            continue
        if document.document_id == document_id:
            return build_note_record(document, kind, include_example=True)

    return None


def classify_note_document(document: IndexDocument) -> Optional[NoteKind]:
    if document.file_type not in {"md", "markdown"}:
        return None

    parts = PurePosixPath(document.relative_path).parts
    if not parts:
        return None

    top_level = parts[0].lower()
    for kind, folder in NOTE_FOLDER_BY_KIND.items():
        if top_level == folder:
            return kind

    return None


def build_note_record(
    document: IndexDocument,
    kind: NoteKind,
    include_example: bool = False,
) -> dict[str, object]:
    sections = extract_markdown_sections(document.content)

    if kind == "role":
        return {
            "id": document.document_id,
            "name": document.title,
            "kind": kind,
            "purpose": first_section_value(sections, "purpose"),
            "boundaries": section_items(sections, "boundaries"),
            "related_skills": section_items(sections, "related skills"),
            "path": document.path,
        }

    record = {
        "id": document.document_id,
        "name": document.title,
        "kind": kind,
        "purpose": first_section_value(sections, "purpose"),
        "trigger": first_section_value(sections, "trigger"),
        "constraints": section_items(sections, "constraints"),
        "related_agents": section_items(sections, "related agents"),
        "path": document.path,
    }
    if include_example:
        record["example"] = first_section_value(sections, "example")
    return record


def extract_markdown_sections(content: str) -> Dict[str, str]:
    sections: Dict[str, str] = {}
    current_heading: str | None = None
    current_lines: List[str] = []

    for line in content.splitlines():
        match = SECTION_PATTERN.match(line.strip())
        if match:
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = match.group(1).strip().lower()
            current_lines = []
            continue

        if current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def first_section_value(sections: Dict[str, str], name: str) -> str:
    items = section_items(sections, name)
    if items:
        return items[0]

    raw_value = sections.get(name.lower(), "").strip()
    if not raw_value:
        return ""

    return " ".join(line.strip() for line in raw_value.splitlines() if line.strip())


def section_items(sections: Dict[str, str], name: str) -> List[str]:
    raw_value = sections.get(name.lower(), "").strip()
    if not raw_value:
        return []

    items: List[str] = []
    for line in raw_value.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            items.append(normalize_note_reference(stripped[2:].strip()))
            continue
        numbered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if numbered_match:
            items.append(normalize_note_reference(numbered_match.group(1).strip()))

    if items:
        return items

    compact_text = " ".join(line.strip() for line in raw_value.splitlines() if line.strip())
    return [normalize_note_reference(compact_text)]


def normalize_note_reference(value: str) -> str:
    wiki_match = WIKI_LINK_PATTERN.match(value)
    if wiki_match:
        return wiki_match.group(1).strip()

    markdown_match = MARKDOWN_LINK_PATTERN.match(value)
    if markdown_match:
        return markdown_match.group(1).strip()

    return value.strip()
