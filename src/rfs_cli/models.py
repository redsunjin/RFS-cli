from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

SourceType = Literal["local", "obsidian", "drive"]
OutputFormat = Literal["text", "json"]


class SourceConfig(BaseModel):
    id: str
    type: SourceType
    root_path: str
    display_name: str
    enabled: bool = True


class AppConfig(BaseModel):
    schema_version: str = "1"
    default_output_format: OutputFormat = "text"
    sources: List[SourceConfig] = Field(default_factory=list)


class ErrorPayload(BaseModel):
    code: str
    message: str


class CommandPayload(BaseModel):
    schema_version: str = "1"
    command: str
    ok: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[ErrorPayload] = None


class IndexDocument(BaseModel):
    document_id: str
    source_id: str
    source_type: SourceType
    path: str
    relative_path: str
    title: str
    file_type: str
    modified_at: int
    content_hash: str
    content: str
    tags: List[str] = Field(default_factory=list)
    aliases: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IndexStore(BaseModel):
    schema_version: str = "1"
    generated_at: str
    documents: List[IndexDocument] = Field(default_factory=list)
