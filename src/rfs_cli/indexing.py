from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rfs_cli.models import IndexDocument, IndexStore, SourceConfig
from rfs_cli.services import build_snippet, iter_text_files

TAG_PATTERN = re.compile(r"(?<!\w)#([A-Za-z0-9_-]+)")
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]+")
SOURCE_PRIORITY = {
    "obsidian": 1.0,
    "local": 0.5,
    "drive": 0.25,
}


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "source"


def build_source_id(root_path: Path) -> str:
    return slugify(root_path.name or root_path.as_posix())


def strip_quotes(value: str) -> str:
    return value.strip().strip('"').strip("'")


def normalize_frontmatter_scalar(value: str) -> Any:
    stripped = value.strip()

    if not stripped:
        return ""

    if stripped.startswith("[") and stripped.endswith("]"):
        parts = [part.strip() for part in stripped[1:-1].split(",")]
        return [strip_quotes(part) for part in parts if strip_quotes(part)]

    lowered = stripped.lower()
    if lowered in {"null", "none"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if re.fullmatch(r"-?\d+", stripped):
        return int(stripped)
    if re.fullmatch(r"-?\d+\.\d+", stripped):
        return float(stripped)

    return strip_quotes(stripped)


def line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_frontmatter_block(
    lines: List[str],
    start: int = 0,
    base_indent: int = 0,
) -> Tuple[Dict[str, Any], int]:
    data: Dict[str, Any] = {}
    index = start

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()

        if not stripped:
            index += 1
            continue

        indent = line_indent(raw_line)
        if indent < base_indent:
            break
        if indent > base_indent:
            index += 1
            continue

        if ":" not in stripped:
            index += 1
            continue

        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        if value:
            data[key] = normalize_frontmatter_scalar(value)
            index += 1
            continue

        index += 1
        child_lines_start = index
        while index < len(lines):
            next_line = lines[index]
            next_stripped = next_line.strip()
            if not next_stripped:
                index += 1
                continue
            if line_indent(next_line) <= base_indent:
                break
            index += 1

        child_lines = lines[child_lines_start:index]
        child_content = [line for line in child_lines if line.strip()]
        if not child_content:
            data[key] = []
            continue

        first_child = child_content[0]
        child_indent = line_indent(first_child)

        if first_child.strip().startswith("- "):
            items: List[Any] = []
            for child_line in child_content:
                if line_indent(child_line) != child_indent:
                    continue
                child_value = child_line.strip()[2:].strip()
                items.append(normalize_frontmatter_scalar(child_value))
            data[key] = items
            continue

        child_data, _ = parse_frontmatter_block(child_content, start=0, base_indent=child_indent)
        data[key] = child_data

    return data, index


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    if not content.startswith("---\n"):
        return {}, content

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, content

    frontmatter_lines: List[str] = []
    body_start = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() in {"---", "..."}:
            body_start = index + 1
            break
        frontmatter_lines.append(line)

    if body_start is None:
        return {}, content

    frontmatter, _ = parse_frontmatter_block(frontmatter_lines, start=0, base_indent=0)

    body = "\n".join(lines[body_start:]).lstrip()
    return frontmatter, body


def normalize_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [strip_quotes(str(item)) for item in value if strip_quotes(str(item))]
    if isinstance(value, str):
        if "," in value:
            return [strip_quotes(part) for part in value.split(",") if strip_quotes(part)]
        stripped = strip_quotes(value)
        return [stripped] if stripped else []
    return [strip_quotes(str(value))]


def extract_title(path: Path, content: str, frontmatter: Dict[str, Any]) -> str:
    title = frontmatter.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped == "---":
            continue
        return stripped[:120]
    alias_list = normalize_string_list(frontmatter.get("aliases") or frontmatter.get("alias"))
    if alias_list:
        return alias_list[0]

    return path.stem


def extract_aliases(frontmatter: Dict[str, Any]) -> List[str]:
    aliases = frontmatter.get("aliases")
    if aliases is None:
        aliases = frontmatter.get("alias")
    return normalize_string_list(aliases)


def normalize_tag(tag: str) -> str:
    return strip_quotes(tag).lstrip("#").strip().lower()


def extract_tags(content: str, frontmatter: Dict[str, Any]) -> List[str]:
    tags = set()

    for tag in normalize_string_list(frontmatter.get("tags")):
        normalized = normalize_tag(tag)
        if normalized:
            tags.add(normalized)

    for match in TAG_PATTERN.findall(content):
        normalized = normalize_tag(match)
        if normalized:
            tags.add(normalized)

    return sorted(tags)


def make_document_id(source_id: str, path: Path) -> str:
    digest = hashlib.sha1(f"{source_id}:{path.resolve()}".encode("utf-8")).hexdigest()
    return digest[:12]


def detect_file_type(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "<no_ext>"


def document_metadata(
    source: SourceConfig,
    root: Path,
    path: Path,
    frontmatter: Dict[str, Any],
    aliases: List[str],
    tags: List[str],
) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {
        "source_display_name": source.display_name,
        "source_priority": SOURCE_PRIORITY.get(source.type, 0.0),
    }

    if source.type == "obsidian":
        metadata["relative_path"] = path.relative_to(root).as_posix()
        metadata["frontmatter"] = frontmatter
        metadata["aliases"] = aliases
        metadata["tags"] = tags

    return metadata


def build_index(sources: List[SourceConfig]) -> IndexStore:
    documents: List[IndexDocument] = []

    for source in sources:
        root = Path(source.root_path).expanduser().resolve()
        for path in iter_text_files(root):
            raw_content = path.read_text(encoding="utf-8", errors="ignore")
            frontmatter, content = extract_frontmatter(raw_content)
            aliases = extract_aliases(frontmatter)
            tags = extract_tags(content, frontmatter)
            relative_path = path.relative_to(root).as_posix()
            documents.append(
                IndexDocument(
                    document_id=make_document_id(source.id, path),
                    source_id=source.id,
                    source_type=source.type,
                    path=str(path.resolve()),
                    relative_path=relative_path,
                    title=extract_title(path, content, frontmatter),
                    file_type=detect_file_type(path),
                    modified_at=int(path.stat().st_mtime),
                    content_hash=hashlib.sha1(content.encode("utf-8")).hexdigest(),
                    content=content,
                    tags=tags,
                    aliases=aliases,
                    metadata=document_metadata(source, root, path, frontmatter, aliases, tags),
                )
            )

    return IndexStore(
        generated_at=datetime.now(timezone.utc).isoformat(),
        documents=documents,
    )


def search_index(
    query: str,
    index_store: IndexStore,
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    tag_filters: Optional[List[str]] = None,
    path_prefix: Optional[str] = None,
    file_type: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, object]]:
    lowered_query = query.lower().strip()
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(lowered_query)] or [lowered_query]
    results: List[Dict[str, object]] = []
    normalized_path_prefix = path_prefix.strip("/").lower() if path_prefix else None
    normalized_file_type = file_type.lower().lstrip(".") if file_type else None
    normalized_tags = [normalize_tag(tag) for tag in (tag_filters or [])]

    for document in index_store.documents:
        if source_type and document.source_type != source_type:
            continue
        if source_id and document.source_id != source_id:
            continue
        if normalized_file_type and document.file_type != normalized_file_type:
            continue
        if (
            normalized_path_prefix
            and not document.relative_path.lower().startswith(normalized_path_prefix)
        ):
            continue
        if normalized_tags and not all(tag in document.tags for tag in normalized_tags):
            continue

        title_lower = document.title.lower()
        path_lower = document.path.lower()
        relative_path_lower = document.relative_path.lower()
        content_lower = document.content.lower()
        aliases_lower = [alias.lower() for alias in document.aliases]
        tags_lower = [tag.lower() for tag in document.tags]

        exact_title = lowered_query in title_lower
        exact_path = lowered_query in path_lower or lowered_query in relative_path_lower
        exact_content = lowered_query in content_lower
        exact_alias = any(lowered_query in alias for alias in aliases_lower)
        exact_tag = any(lowered_query in tag for tag in tags_lower)

        token_hits = {
            "title": sum(1 for token in tokens if token and token in title_lower),
            "alias": sum(
                1 for token in tokens if token and any(token in alias for alias in aliases_lower)
            ),
            "tag": sum(1 for token in tokens if token and any(token in tag for tag in tags_lower)),
            "path": sum(1 for token in tokens if token and token in relative_path_lower),
            "content": sum(1 for token in tokens if token and token in content_lower),
        }
        matched_tokens = sum(
            1
            for token in tokens
            if token
            and any(
                [
                    token in title_lower,
                    token in relative_path_lower,
                    token in content_lower,
                    any(token in alias for alias in aliases_lower),
                    any(token in tag for tag in tags_lower),
                ]
            )
        )
        minimum_token_matches = 1 if len(tokens) == 1 else 2

        matches_query = any(
            [exact_title, exact_path, exact_content, exact_alias, exact_tag, *token_hits.values()]
        )
        if not matches_query or matched_tokens < minimum_token_matches:
            continue

        score = 0.0
        if exact_title:
            score += 8.0
        if exact_alias:
            score += 6.0
        if exact_tag:
            score += 5.0
        if exact_path:
            score += 4.0
        if exact_content:
            score += 2.0

        score += SOURCE_PRIORITY.get(document.source_type, 0.0)
        score += token_hits["title"] * 2.5
        score += token_hits["alias"] * 2.0
        score += token_hits["tag"] * 1.75
        score += token_hits["path"] * 1.25
        score += min(token_hits["content"], 5) * 0.5
        if tokens and all(token in content_lower for token in tokens):
            score += 1.0
        if tokens and all(token in title_lower for token in tokens):
            score += 2.0

        results.append(
            {
                "document_id": document.document_id,
                "path": document.path,
                "relative_path": document.relative_path,
                "title": document.title,
                "source_id": document.source_id,
                "source_type": document.source_type,
                "file_type": document.file_type,
                "score": score,
                "snippet": build_snippet(document.content, query),
                "tags": document.tags,
                "aliases": document.aliases,
                "metadata": document.metadata,
            }
        )

    return sorted(results, key=lambda item: (-item["score"], item["title"]))[:limit]


def resolve_index_document(target: str, index_store: IndexStore) -> Optional[IndexDocument]:
    resolved_target = Path(target).expanduser().resolve() if Path(target).exists() else None

    for document in index_store.documents:
        if document.document_id == target:
            return document
        if resolved_target and Path(document.path).resolve() == resolved_target:
            return document

    return None
