from __future__ import annotations

import json
import os
from typing import Any, Optional
from urllib import error, request

from rfs_cli.models import LLMConfig

SYSTEM_PROMPT = """You are the built-in assistant for rfs-cli.

Your job is to help the user use the CLI effectively.

Rules:
- Answer in Korean unless the user clearly asks in another language.
- Prefer concrete commands over abstract explanation.
- Do not invent commands that are not supported.
- If a feature is not implemented yet, say so directly.
- When helpful, show 1-3 commands in code blocks.

Supported commands:
- rfs index add <root> --source local|obsidian
- rfs index sources
- rfs index run [--source ...] [--format json]
- rfs search <query> [--source ...] [--source-id ...] [--tag ...]
  [--path-prefix ...] [--file-type ...] [--format json]
- rfs show <document-id|path> [--metadata-only] [--preview-chars N] [--format json]
- rfs dev git-summary [--path PATH] [--format json]
- rfs dev project-stats [--path PATH] [--format json]
- rfs dev find-todo [--path PATH] [--format json]
- rfs agent list-files <root> [--format json]
- rfs agent find-text <query> <root> [--format json]
- rfs llm setup
- rfs llm status
- rfs ask "<question>"

Not implemented yet:
- Google Drive search is still a placeholder.
"""

PROVIDER_ALIASES = {
    "ollama": "ollama",
    "lmstudio": "lmstudio",
    "lm-studio": "lmstudio",
    "openai-compatible": "openai-compatible",
    "openai_compatible": "openai-compatible",
    "openai": "openai-compatible",
    "generic": "openai-compatible",
}


def normalize_provider(value: str) -> str:
    normalized = PROVIDER_ALIASES.get(value.strip().lower())
    if normalized is None:
        raise ValueError(
            "Unsupported provider. Choose one of: ollama, lmstudio, openai-compatible."
        )
    return normalized


def default_base_url(provider: str) -> str:
    if provider == "ollama":
        return "http://127.0.0.1:11434"
    if provider == "lmstudio":
        return "http://127.0.0.1:1234"
    return "https://api.openai.com"


def default_model_hint(provider: str) -> str:
    if provider == "ollama":
        return "qwen2.5:7b-instruct"
    if provider == "lmstudio":
        return "local-model"
    return "gpt-4o-mini"


def default_api_key_env(provider: str) -> Optional[str]:
    if provider == "openai-compatible":
        return "OPENAI_API_KEY"
    return None


def auth_headers(config: LLMConfig) -> dict[str, str]:
    headers: dict[str, str] = {}
    if config.api_key_env:
        api_key = os.environ.get(config.api_key_env)
        if not api_key:
            raise ValueError(
                f'Environment variable "{config.api_key_env}" is not set '
                "for the configured API key."
            )
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def request_json(
    method: str,
    url: str,
    payload: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    encoded = None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if payload is not None:
        encoded = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    http_request = request.Request(
        url,
        data=encoded,
        headers=request_headers,
        method=method.upper(),
    )

    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = body.strip() or exc.reason
        raise ValueError(f"HTTP {exc.code} from {url}: {message[:200]}") from exc
    except error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise ValueError(f"Could not reach {url}: {reason}") from exc

    if not body.strip():
        return {}

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON returned from {url}.") from exc


def get_llm_status(config: LLMConfig) -> dict[str, Any]:
    status: dict[str, Any] = {
        "configured": True,
        "provider": config.provider,
        "base_url": config.base_url,
        "model": config.model,
        "api_key_env": config.api_key_env,
        "api_key_present": bool(os.environ.get(config.api_key_env)) if config.api_key_env else None,
        "reachable": False,
        "available_models": [],
        "default_model_available": None,
        "error": None,
    }

    try:
        if config.provider == "ollama":
            response = request_json("GET", f"{config.base_url.rstrip('/')}/api/tags")
            models = [
                item.get("name") or item.get("model")
                for item in response.get("models", [])
                if item.get("name") or item.get("model")
            ]
        else:
            response = request_json(
                "GET",
                f"{config.base_url.rstrip('/')}/v1/models",
                headers=auth_headers(config),
            )
            models = [
                item.get("id")
                for item in response.get("data", [])
                if item.get("id")
            ]
    except ValueError as exc:
        status["error"] = str(exc)
        return status

    status["reachable"] = True
    status["available_models"] = models
    status["default_model_available"] = config.model in models if models else None
    return status


def extract_message_content(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part for part in parts if part).strip()
    return ""


def history_to_messages(history: Optional[list[dict[str, str]]] = None) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history or []:
        role = item.get("role")
        content = item.get("content", "").strip()
        if role not in {"user", "assistant", "system"} or not content:
            continue
        messages.append({"role": role, "content": content})
    return messages


def ask_llm(
    config: LLMConfig,
    question: str,
    history: Optional[list[dict[str, str]]] = None,
) -> str:
    messages = history_to_messages(history)
    messages.append({"role": "user", "content": question})
    if config.provider == "ollama":
        response = request_json(
            "POST",
            f"{config.base_url.rstrip('/')}/api/chat",
            payload={"model": config.model, "messages": messages, "stream": False},
        )
        answer = extract_message_content(response.get("message", {}).get("content"))
    else:
        response = request_json(
            "POST",
            f"{config.base_url.rstrip('/')}/v1/chat/completions",
            payload={"model": config.model, "messages": messages, "temperature": 0.2},
            headers=auth_headers(config),
        )
        choices = response.get("choices", [])
        message = choices[0].get("message", {}) if choices else {}
        answer = extract_message_content(message.get("content"))

    if not answer:
        raise ValueError("The configured LLM returned an empty response.")

    return answer
