from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from rfs_cli.config import ensure_parent
from rfs_cli.models import IndexDocument, ResearchExportDocument, ResearchExportManifest

SAFE_EXPORT_NAME = re.compile(r"[^a-z0-9]+")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify_export_name(value: str) -> str:
    normalized = SAFE_EXPORT_NAME.sub("-", value.lower()).strip("-")
    return normalized or "document"


def document_export_name(position: int, document: IndexDocument) -> str:
    base = slugify_export_name(document.title or Path(document.path).stem)
    suffix = Path(document.path).suffix
    extension = suffix if suffix else ".txt"
    return f"{position:02d}-{base}{extension}"


def build_research_filters(
    source_type: Optional[str],
    source_id: Optional[str],
    tags: Optional[List[str]],
    path_prefix: Optional[str],
    file_type: Optional[str],
    limit: int,
) -> Dict[str, Any]:
    return {
        "source_type": source_type,
        "source_id": source_id,
        "tags": tags or [],
        "path_prefix": path_prefix,
        "file_type": file_type,
        "limit": limit,
    }


def export_research_bundle(
    query: str,
    documents: List[IndexDocument],
    snippets_by_id: Dict[str, str],
    output_dir: Path,
    filters: Dict[str, Any],
) -> tuple[Path, Path, ResearchExportManifest]:
    resolved_output_dir = output_dir.expanduser().resolve()
    documents_dir = resolved_output_dir / "documents"
    ensure_parent(documents_dir / ".keep")
    documents_dir.mkdir(parents=True, exist_ok=True)

    manifest_documents: List[ResearchExportDocument] = []

    for position, document in enumerate(documents, start=1):
        export_name = document_export_name(position, document)
        export_path = documents_dir / export_name
        export_path.write_text(document.content, encoding="utf-8")
        manifest_documents.append(
            ResearchExportDocument(
                document_id=document.document_id,
                title=document.title,
                source_id=document.source_id,
                source_type=document.source_type,
                relative_path=document.relative_path,
                original_path=document.path,
                export_path=str(export_path),
                file_type=document.file_type,
                snippet=snippets_by_id.get(document.document_id, ""),
                tags=document.tags,
                aliases=document.aliases,
                metadata=document.metadata,
                modified_at=document.modified_at,
                content_hash=document.content_hash,
            )
        )

    manifest = ResearchExportManifest(
        created_at=utc_now_iso(),
        query=query,
        filters=filters,
        item_count=len(manifest_documents),
        documents=manifest_documents,
    )
    manifest_path = resolved_output_dir / "manifest.json"
    ensure_parent(manifest_path)
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return resolved_output_dir, manifest_path, manifest
