from __future__ import annotations

import json
import os
import warnings
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from urllib import error, parse, request

from rfs_cli.config import (
    ensure_parent,
    load_drive_cache,
    resolve_drive_cache_path,
    resolve_drive_token_path,
    resolve_state_dir,
    save_drive_cache,
)
from rfs_cli.models import DriveCacheEntry, DriveCacheStore, DriveConfig, DriveFileRecord

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials

DRIVE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
DRIVE_TOKEN_URI = "https://oauth2.googleapis.com/token"
DRIVE_FILES_URI = "https://www.googleapis.com/drive/v3/files"
DRIVE_REDIRECT_URIS = [
    "http://127.0.0.1",
    "http://localhost",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_google_drive_modules() -> tuple[Any, Any]:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"You are using a Python version 3\.9 past its end of life.*",
            category=FutureWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 v2 only supports OpenSSL 1\.1\.1\+.*",
            category=Warning,
        )
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

    return Credentials, InstalledAppFlow


def load_google_request_class() -> Any:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"You are using a Python version 3\.9 past its end of life.*",
            category=FutureWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=r"urllib3 v2 only supports OpenSSL 1\.1\.1\+.*",
            category=Warning,
        )
        from google.auth.transport.requests import Request

    return Request


def require_drive_client_secrets(drive_config: DriveConfig) -> tuple[str, str]:
    client_id = os.environ.get(drive_config.auth.client_id_env)
    client_secret = os.environ.get(drive_config.auth.client_secret_env)
    missing: list[str] = []
    if not client_id:
        missing.append(drive_config.auth.client_id_env)
    if not client_secret:
        missing.append(drive_config.auth.client_secret_env)
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing Google Drive client secret env var(s): {joined}")
    return client_id, client_secret


def build_drive_client_config(drive_config: DriveConfig) -> dict[str, Any]:
    client_id, client_secret = require_drive_client_secrets(drive_config)
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": DRIVE_AUTH_URI,
            "token_uri": DRIVE_TOKEN_URI,
            "redirect_uris": DRIVE_REDIRECT_URIS,
        }
    }


def build_env_authorized_user_info(drive_config: DriveConfig) -> Optional[dict[str, Any]]:
    refresh_token = os.environ.get(drive_config.auth.refresh_token_env)
    if not refresh_token:
        return None

    client_id, client_secret = require_drive_client_secrets(drive_config)
    return {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "token_uri": DRIVE_TOKEN_URI,
        "scopes": drive_config.auth.scopes,
    }


def load_drive_credentials(
    drive_config: DriveConfig,
    state_dir: Path,
) -> tuple[Optional[Credentials], Optional[str], Path]:
    Credentials, _ = load_google_drive_modules()
    resolved_state_dir = resolve_state_dir(state_dir)
    token_path = resolve_drive_token_path(state_dir=resolved_state_dir)
    if token_path.exists():
        try:
            credentials = Credentials.from_authorized_user_file(
                str(token_path),
                scopes=drive_config.auth.scopes,
            )
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid Google Drive token file: {token_path}") from exc
        return credentials, "state_file", token_path

    user_info = build_env_authorized_user_info(drive_config)
    if user_info is None:
        return None, None, token_path

    credentials = Credentials.from_authorized_user_info(
        user_info,
        scopes=drive_config.auth.scopes,
    )
    return credentials, "env_refresh_token", token_path


def save_drive_credentials(credentials: Credentials, state_dir: Path) -> Path:
    token_path = resolve_drive_token_path(state_dir=resolve_state_dir(state_dir))
    ensure_parent(token_path)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return token_path


def run_drive_installed_app_auth(
    drive_config: DriveConfig,
    state_dir: Path,
    open_browser: bool = True,
    port: int = 0,
) -> Path:
    _, InstalledAppFlow = load_google_drive_modules()
    flow = InstalledAppFlow.from_client_config(
        build_drive_client_config(drive_config),
        scopes=drive_config.auth.scopes,
    )
    credentials = flow.run_local_server(
        port=port,
        open_browser=open_browser,
        authorization_prompt_message=(
            "Open this URL to authorize rfs-cli for Google Drive access:\n{url}\n"
        ),
        success_message="rfs-cli Google Drive authorization completed. You can close this window.",
    )
    return save_drive_credentials(credentials, state_dir)


def ensure_drive_credentials(
    drive_config: DriveConfig,
    state_dir: Path,
) -> tuple[Credentials, str, Path]:
    credentials, auth_source, token_path = load_drive_credentials(drive_config, state_dir)
    if credentials is None:
        raise ValueError("Google Drive is not authenticated. Run `rfs drive auth` first.")

    if credentials.token and not credentials.expired:
        return credentials, auth_source or "unknown", token_path

    if not credentials.refresh_token:
        raise ValueError(
            "Google Drive credentials are missing a refresh token. Run `rfs drive auth` again."
        )

    Request = load_google_request_class()
    try:
        credentials.refresh(Request())
    except Exception as exc:  # pragma: no cover - provider/library defensive path
        raise ValueError(f"Failed to refresh Google Drive credentials: {exc}") from exc

    if auth_source == "state_file":
        save_drive_credentials(credentials, state_dir)

    return credentials, auth_source or "unknown", token_path


def escape_drive_query_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def build_drive_fields(drive_config: DriveConfig) -> str:
    fields: list[str] = []
    for field_name in [*drive_config.metadata_fields, "id", "name", "mimeType", "modifiedTime"]:
        if field_name not in fields:
            fields.append(field_name)
    return f"nextPageToken,incompleteSearch,files({','.join(fields)})"


def drive_search_query(query: str) -> str:
    normalized = query.strip()
    if not normalized:
        raise ValueError("Google Drive query cannot be empty.")
    escaped = escape_drive_query_literal(normalized)
    return f"trashed = false and name contains '{escaped}'"


def drive_search_url(
    drive_config: DriveConfig,
    query: str,
    page_size: int,
    page_token: Optional[str] = None,
) -> str:
    corpora = drive_config.corpora[0] if drive_config.corpora else "user"
    params: dict[str, object] = {
        "q": drive_search_query(query),
        "fields": build_drive_fields(drive_config),
        "pageSize": page_size,
        "corpora": corpora,
    }
    if page_token:
        params["pageToken"] = page_token
    if drive_config.include_shared_drives:
        params["includeItemsFromAllDrives"] = "true"
        params["supportsAllDrives"] = "true"
    return f"{DRIVE_FILES_URI}?{parse.urlencode(params)}"


def request_drive_json(url: str, access_token: str, timeout: float = 30.0) -> dict[str, Any]:
    http_request = request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            message = body or f"HTTP {exc.code}"
        else:
            message = (
                parsed.get("error", {}).get("message")
                or parsed.get("error_description")
                or body
                or f"HTTP {exc.code}"
            )
        raise ValueError(f"Google Drive API request failed: {message}") from exc
    except error.URLError as exc:
        raise ValueError(f"Google Drive API request failed: {exc.reason}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError("Google Drive API returned invalid JSON.") from exc


def parse_drive_file_record(item: dict[str, Any]) -> DriveFileRecord:
    raw_size = item.get("size")
    size_bytes: Optional[int] = None
    if isinstance(raw_size, int):
        size_bytes = raw_size
    elif isinstance(raw_size, str) and raw_size.isdigit():
        size_bytes = int(raw_size)

    return DriveFileRecord(
        file_id=item.get("id", ""),
        name=item.get("name", ""),
        mime_type=item.get("mimeType", ""),
        modified_time=item.get("modifiedTime", ""),
        web_view_link=item.get("webViewLink"),
        drive_id=item.get("driveId"),
        parents=[str(parent) for parent in item.get("parents", [])],
        size_bytes=size_bytes,
    )


def drive_cache_key(
    drive_config: DriveConfig,
    query: str,
    page_size: int,
    page_token: Optional[str] = None,
) -> str:
    payload = {
        "query": query.strip(),
        "page_size": page_size,
        "page_token": page_token,
        "corpora": drive_config.corpora,
        "include_shared_drives": drive_config.include_shared_drives,
        "metadata_fields": drive_config.metadata_fields,
    }
    digest = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"drive:{digest}"


def load_drive_cache_or_default(state_dir: Path) -> DriveCacheStore:
    try:
        return load_drive_cache(state_dir=state_dir) or DriveCacheStore()
    except ValueError:
        return DriveCacheStore()


def prune_drive_cache_entries(
    entries: list[DriveCacheEntry],
    now: datetime,
) -> list[DriveCacheEntry]:
    valid_entries: list[DriveCacheEntry] = []
    for entry in entries:
        try:
            expires_at = parse_timestamp(entry.expires_at)
        except ValueError:
            continue
        if expires_at > now:
            valid_entries.append(entry)
    valid_entries.sort(key=lambda entry: entry.fetched_at, reverse=True)
    return valid_entries


def resolve_cached_drive_entry(
    drive_config: DriveConfig,
    state_dir: Path,
    query: str,
    page_size: int,
    page_token: Optional[str] = None,
) -> tuple[Optional[DriveCacheEntry], Path]:
    cache_path = resolve_drive_cache_path(state_dir=state_dir)
    if drive_config.cache.mode == "disabled":
        return None, cache_path

    cache_store = load_drive_cache_or_default(state_dir)
    key = drive_cache_key(drive_config, query=query, page_size=page_size, page_token=page_token)
    now = utc_now()
    pruned_entries = prune_drive_cache_entries(cache_store.entries, now)
    if len(pruned_entries) != len(cache_store.entries):
        save_drive_cache(DriveCacheStore(entries=pruned_entries), state_dir=state_dir)

    for entry in pruned_entries:
        if entry.key == key:
            return entry, cache_path
    return None, cache_path


def store_drive_cache_entry(
    drive_config: DriveConfig,
    state_dir: Path,
    query: str,
    page_size: int,
    auth_source: str,
    records: list[DriveFileRecord],
    next_page_token: Optional[str],
    incomplete_search: bool,
    page_token: Optional[str] = None,
) -> tuple[Path, DriveCacheEntry]:
    cache_path = resolve_drive_cache_path(state_dir=state_dir)
    if drive_config.cache.mode == "disabled":
        cache_key = drive_cache_key(
            drive_config,
            query=query,
            page_size=page_size,
            page_token=page_token,
        )
        entry = DriveCacheEntry(
            key=cache_key,
            query=query,
            page_size=page_size,
            page_token=page_token,
            auth_source=auth_source,
            fetched_at=utc_now().isoformat(),
            expires_at=utc_now().isoformat(),
            next_page_token=next_page_token,
            incomplete_search=incomplete_search,
            records=records,
        )
        return cache_path, entry

    now = utc_now()
    expires_at = now + timedelta(minutes=drive_config.cache.ttl_minutes)
    entry = DriveCacheEntry(
        key=drive_cache_key(drive_config, query=query, page_size=page_size, page_token=page_token),
        query=query,
        page_size=page_size,
        page_token=page_token,
        auth_source=auth_source,
        fetched_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
        next_page_token=next_page_token,
        incomplete_search=incomplete_search,
        records=records,
    )
    cache_store = load_drive_cache_or_default(state_dir)
    remaining = [
        existing
        for existing in prune_drive_cache_entries(cache_store.entries, now)
        if existing.key != entry.key
    ]
    remaining.insert(0, entry)
    save_drive_cache(
        DriveCacheStore(entries=remaining[: drive_config.cache.max_entries]),
        state_dir=state_dir,
    )
    return cache_path, entry


def fetch_drive_file_metadata(
    drive_config: DriveConfig,
    state_dir: Path,
    query: str,
    page_size: int = 20,
    page_token: Optional[str] = None,
) -> dict[str, Any]:
    if page_size < 1:
        raise ValueError("Google Drive page size must be at least 1.")

    resolved_state_dir = resolve_state_dir(state_dir)
    cached_entry, cache_path = resolve_cached_drive_entry(
        drive_config,
        resolved_state_dir,
        query=query,
        page_size=page_size,
        page_token=page_token,
    )
    if cached_entry is not None:
        return {
            "query": query,
            "page_size": page_size,
            "next_page_token": cached_entry.next_page_token,
            "incomplete_search": cached_entry.incomplete_search,
            "auth_source": cached_entry.auth_source,
            "token_path": str(resolve_drive_token_path(state_dir=resolved_state_dir)),
            "cache_path": str(cache_path),
            "cache_key": cached_entry.key,
            "cache_hit": True,
            "fetched_at": cached_entry.fetched_at,
            "expires_at": cached_entry.expires_at,
            "records": cached_entry.records,
        }

    credentials, auth_source, token_path = ensure_drive_credentials(drive_config, state_dir)
    if not credentials.token:
        raise ValueError("Google Drive credentials do not have an access token yet.")

    response = request_drive_json(
        drive_search_url(drive_config, query=query, page_size=page_size, page_token=page_token),
        access_token=credentials.token,
    )
    records = [parse_drive_file_record(item) for item in response.get("files", [])]
    cache_path, cache_entry = store_drive_cache_entry(
        drive_config,
        resolved_state_dir,
        query=query,
        page_size=page_size,
        auth_source=auth_source,
        records=records,
        next_page_token=response.get("nextPageToken"),
        incomplete_search=bool(response.get("incompleteSearch", False)),
        page_token=page_token,
    )
    return {
        "query": query,
        "page_size": page_size,
        "next_page_token": response.get("nextPageToken"),
        "incomplete_search": bool(response.get("incompleteSearch", False)),
        "auth_source": auth_source,
        "token_path": str(token_path),
        "cache_path": str(cache_path),
        "cache_key": cache_entry.key,
        "cache_hit": False,
        "fetched_at": cache_entry.fetched_at,
        "expires_at": cache_entry.expires_at,
        "records": records,
    }
