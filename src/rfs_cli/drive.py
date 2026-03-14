from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from rfs_cli.config import ensure_parent, resolve_drive_token_path, resolve_state_dir
from rfs_cli.models import DriveConfig

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials

DRIVE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
DRIVE_TOKEN_URI = "https://oauth2.googleapis.com/token"
DRIVE_REDIRECT_URIS = [
    "http://127.0.0.1",
    "http://localhost",
]


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
