from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from rfs_cli.config import ensure_parent, resolve_state_dir
from rfs_cli.indexing import search_index
from rfs_cli.models import IndexDocument, IndexStore


def research_export_slug(query: str) -> str:
    slug = re.sub(r"[^\w]+", "-", query.strip().lower(), flags=re.UNICODE).strip("-_")
    return slug or "research-export"


def research_export_timestamp(now: Optional[datetime] = None) -> str:
    current = now or datetime.now(timezone.utc)
    return current.strftime("%Y%m%d-%H%M%SZ")


def load_export_content(document: IndexDocument) -> tuple[str, str]:
    source_path = Path(document.path)
    if source_path.exists():
        return source_path.read_text(encoding="utf-8", errors="ignore"), "source_file"
    return document.content, "index_snapshot"


def export_research_bundle(
    *,
    query: str,
    index_store: IndexStore,
    output_dir: Path,
    state_dir: Path,
    source: Optional[str] = None,
    source_id: Optional[str] = None,
    tag_filters: Optional[list[str]] = None,
    path_prefix: Optional[str] = None,
    file_type: Optional[str] = None,
    limit: int = 20,
) -> Optional[dict[str, Any]]:
    results = search_index(
        query=query,
        index_store=index_store,
        source_type=source,
        source_id=source_id,
        tag_filters=tag_filters,
        path_prefix=path_prefix,
        file_type=file_type,
        limit=limit,
    )
    if not results:
        return None

    document_map = {document.document_id: document for document in index_store.documents}
    export_root = output_dir.expanduser().resolve()
    bundle_name = f"{research_export_slug(query)}-{research_export_timestamp()}"
    export_path = export_root / bundle_name
    exported_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    exported_documents: list[dict[str, Any]] = []
    for result in results:
        document = document_map[result["document_id"]]
        relative_export_path = Path("documents") / document.source_id / Path(document.relative_path)
        target_path = export_path / relative_export_path
        ensure_parent(target_path)
        content, content_source = load_export_content(document)
        target_path.write_text(content, encoding="utf-8")
        exported_documents.append(
            {
                "document_id": document.document_id,
                "title": document.title,
                "source_id": document.source_id,
                "source_type": document.source_type,
                "relative_path": document.relative_path,
                "export_path": str(target_path),
                "file_type": document.file_type,
                "tags": document.tags,
                "aliases": document.aliases,
                "metadata": document.metadata,
                "content_source": content_source,
            }
        )

    manifest = {
        "schema_version": "1",
        "bundle_type": "research_export",
        "query": query,
        "exported_at": exported_at,
        "state_dir": str(resolve_state_dir(state_dir)),
        "filters": {
            "source": source,
            "source_id": source_id,
            "tags": tag_filters or [],
            "path_prefix": path_prefix,
            "file_type": file_type,
            "limit": limit,
        },
        "document_count": len(exported_documents),
        "documents": exported_documents,
    }
    manifest_path = export_path / "manifest.json"
    ensure_parent(manifest_path)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "query": query,
        "bundle_name": bundle_name,
        "exported_at": exported_at,
        "state_dir": str(resolve_state_dir(state_dir)),
        "filters": manifest["filters"],
        "document_count": len(exported_documents),
        "export_dir": str(export_path),
        "manifest_path": str(manifest_path),
        "documents": exported_documents,
    }
