from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

SourceType = Literal["local", "obsidian", "drive"]
OutputFormat = Literal["text", "json"]
LLMProvider = Literal["ollama", "lmstudio", "openai-compatible"]
DriveAuthFlow = Literal["oauth-installed-app"]
DriveCacheMode = Literal["disabled", "metadata-only"]


class SourceConfig(BaseModel):
    id: str
    type: SourceType
    root_path: str
    display_name: str
    enabled: bool = True


class LLMConfig(BaseModel):
    provider: LLMProvider
    base_url: str
    model: str
    api_key_env: Optional[str] = None
    enabled: bool = True


class DriveAuthConfig(BaseModel):
    flow: DriveAuthFlow = "oauth-installed-app"
    client_id_env: str = "GOOGLE_DRIVE_CLIENT_ID"
    client_secret_env: str = "GOOGLE_DRIVE_CLIENT_SECRET"
    refresh_token_env: str = "GOOGLE_DRIVE_REFRESH_TOKEN"
    scopes: List[str] = Field(
        default_factory=lambda: ["https://www.googleapis.com/auth/drive.metadata.readonly"]
    )


class DriveCacheConfig(BaseModel):
    mode: DriveCacheMode = "metadata-only"
    ttl_minutes: int = 60
    max_entries: int = 1000


class DriveConfig(BaseModel):
    enabled: bool = True
    include_shared_drives: bool = False
    corpora: List[str] = Field(default_factory=lambda: ["user"])
    metadata_fields: List[str] = Field(
        default_factory=lambda: [
            "id",
            "name",
            "mimeType",
            "modifiedTime",
            "parents",
            "driveId",
            "webViewLink",
            "size",
        ]
    )
    auth: DriveAuthConfig = Field(default_factory=DriveAuthConfig)
    cache: DriveCacheConfig = Field(default_factory=DriveCacheConfig)


class ShellEvent(BaseModel):
    kind: Literal["user", "assistant", "tool", "system"]
    content: str
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ShellMemory(BaseModel):
    schema_version: str = "1"
    session_id: str
    created_at: str
    updated_at: str
    events: List[ShellEvent] = Field(default_factory=list)


class AppConfig(BaseModel):
    schema_version: str = "1"
    default_output_format: OutputFormat = "text"
    sources: List[SourceConfig] = Field(default_factory=list)
    llm: Optional[LLMConfig] = None
    drive: Optional[DriveConfig] = None


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


class DriveFileRecord(BaseModel):
    file_id: str
    name: str
    mime_type: str
    modified_time: str
    web_view_link: Optional[str] = None
    drive_id: Optional[str] = None
    parents: List[str] = Field(default_factory=list)
    size_bytes: Optional[int] = None


class DriveCacheEntry(BaseModel):
    key: str
    query: str
    page_size: int
    page_token: Optional[str] = None
    auth_source: Optional[str] = None
    fetched_at: str
    expires_at: str
    next_page_token: Optional[str] = None
    incomplete_search: bool = False
    records: List[DriveFileRecord] = Field(default_factory=list)


class DriveCacheStore(BaseModel):
    schema_version: str = "1"
    entries: List[DriveCacheEntry] = Field(default_factory=list)
