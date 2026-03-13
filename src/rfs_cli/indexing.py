from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from rfs_cli.models import IndexDocument, IndexStore, SourceConfig
from rfs_cli.services import build_snippet, iter_text_files

TAG_PATTERN = re.compile(r"(?<!\w)#([A-Za-z0-9_-]+)")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "source"


def build_source_id(root_path: Path) -> str:
    return slugify(root_path.name or root_path.as_posix())


def extract_title(path: Path, content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped == "---":
            continue
        return stripped[:120]
    return path.stem


def extract_tags(content: str) -> List[str]:
    tags = set()

    if content.startswith("---\n"):
        end = content.find("\n---", 4)
        if end != -1:
            frontmatter = content[4:end].splitlines()
            for line in frontmatter:
                if not line.strip().startswith("tags:"):
                    continue
                _, raw_value = line.split(":", 1)
                cleaned = raw_value.strip().strip("[]")
                for tag in cleaned.split(","):
                    normalized = tag.strip().strip('"').strip("'")
                    if normalized:
                        tags.add(normalized)

    for match in TAG_PATTERN.findall(content):
        tags.add(match)

    return sorted(tags)


def make_document_id(source_id: str, path: Path) -> str:
    digest = hashlib.sha1(f"{source_id}:{path.resolve()}".encode("utf-8")).hexdigest()
    return digest[:12]


def build_index(sources: List[SourceConfig]) -> IndexStore:
    documents: List[IndexDocument] = []

    for source in sources:
        root = Path(source.root_path).expanduser().resolve()
        for path in iter_text_files(root):
            content = path.read_text(encoding="utf-8", errors="ignore")
            documents.append(
                IndexDocument(
                    document_id=make_document_id(source.id, path),
                    source_id=source.id,
                    source_type=source.type,
                    path=str(path.resolve()),
                    title=extract_title(path, content),
                    modified_at=int(path.stat().st_mtime),
                    content_hash=hashlib.sha1(content.encode("utf-8")).hexdigest(),
                    content=content,
                    tags=extract_tags(content),
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
    limit: int = 20,
) -> List[Dict[str, object]]:
    lowered_query = query.lower()
    results: List[Dict[str, object]] = []

    for document in index_store.documents:
        if source_type and document.source_type != source_type:
            continue

        title_match = lowered_query in document.title.lower()
        path_match = lowered_query in document.path.lower()
        content_match = lowered_query in document.content.lower()
        tag_match = any(lowered_query in tag.lower() for tag in document.tags)

        if not any([title_match, path_match, content_match, tag_match]):
            continue

        score = 0.0
        if title_match:
            score += 3.0
        if path_match:
            score += 2.0
        if tag_match:
            score += 1.5
        if content_match:
            score += 1.0

        results.append(
            {
                "document_id": document.document_id,
                "path": document.path,
                "title": document.title,
                "source_id": document.source_id,
                "source_type": document.source_type,
                "score": score,
                "snippet": build_snippet(document.content, query),
                "tags": document.tags,
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
