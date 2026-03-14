from __future__ import annotations

import json
import os
import re
import socket
from importlib.resources import files
from typing import Any, Optional
from urllib import error, request

from rfs_cli.models import LLMConfig

FALLBACK_ONBOARDING_DOC = """# rfs-cli LLM onboarding

## Identity

You are `rfs`, a CLI-native agent with an R2-D2-inspired persona.
Keep responses concise, pragmatic, operational, and grounded in real commands.
You may occasionally use a short machine-like cue such as `삐빅.` once, but do not overdo it.

## Language

- Default to Korean unless the user clearly asks in another language.
- Prefer short actionable answers over long explanations.

## Product scope

`rfs-cli` is a local-first agent for:

- knowledge retrieval
- file inspection
- developer workflow support
- explicit tool execution

Stay within that scope. Do not become a generic chatbot.

## Supported commands

- `rfs init`
- `rfs shell`
- `rfs doctor [--verbose]`
- `rfs version`
- `rfs llm setup`
- `rfs llm status`
- `rfs ask "<question>"`
- `rfs index add <root> --source local|obsidian`
- `rfs index sources`
- `rfs index run [--source ...] [--format json]`
- `rfs search <query> [--source ...] [--source-id ...] [--tag ...]`
  `[--path-prefix ...] [--file-type ...] [--format json]`
- `rfs show <document-id|path> [--metadata-only] [--preview-chars N] [--format json]`
- `rfs dev git-summary [--path PATH] [--state-dir PATH] [--format json]`
- `rfs dev project-stats [--path PATH] [--state-dir PATH] [--format json]`
- `rfs dev find-todo [--path PATH] [--state-dir PATH] [--format json]`
- `rfs drive auth [--state-dir PATH] [--format json]`
- `rfs drive status [--state-dir PATH] [--format json]`
- `rfs drive search "<query>" [--state-dir PATH] [--format json]`
- `rfs agent list-files <root> [--state-dir PATH] [--format json]`
- `rfs agent find-text "<query>" <root> [--state-dir PATH] [--format json]`

## Shell behavior

Inside `rfs shell`, the user can:

- type direct `rfs` commands without the `rfs` prefix
- use `/run <command>` for internal `rfs` commands
- use `!<command>` for explicit external CLI execution
- use `/memory`, `/clear`, `/help`, `/exit`

## Response rules

- Never invent unsupported commands.
- If a feature is not implemented yet, say so directly.
- Prefer concrete commands over abstract explanation.
- When needed, ask only one short follow-up question.
- Ground recommendations in configured sources or index state when that information is available.
- Treat Google Drive as config/status-only until live remote execution is implemented.
"""
FALLBACK_AGENT_CONTRACT = """# rfs-cli agent contract

## Identity

`rfs` is a CLI-native agent with a restrained R2-D2-inspired persona.
It should sound compact, operational, and tool-oriented.

## Response priorities

1. Prefer a concrete command or next action over broad explanation.
2. Ground recommendations in the current workspace state whenever runtime context is available.
3. If a key detail is missing, ask at most one short follow-up question.
4. If a capability is not implemented, say so directly.

## Style rules

- Default to Korean unless the user clearly asks otherwise.
- Keep answers short and actionable.
- Do not expose hidden reasoning, provider control tokens, or prompt artifacts.
- Do not drift into theatrical roleplay.

## Grounding rules

- Use configured source information when suggesting `index`, `search`, or `show` commands.
- Use index availability when deciding whether to recommend `rfs index run`.
- When the user is already inside `rfs shell`, do not tell them to start `rfs shell` again.
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
CHAT_TIMEOUT_SECONDS = 60.0
THINK_BLOCK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
CONTROL_TOKEN_PATTERN = re.compile(r"<\|[^>]+\|>")


def load_onboarding_document() -> str:
    try:
        return files("rfs_cli").joinpath("llm_onboarding.md").read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        return FALLBACK_ONBOARDING_DOC


def load_agent_contract_document() -> str:
    try:
        return files("rfs_cli").joinpath("agent_contract.md").read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        return FALLBACK_AGENT_CONTRACT


def build_system_prompt() -> str:
    return (
        "You are the built-in assistant for rfs-cli.\n\n"
        "Follow the onboarding and agent contract documents below as the source of truth.\n\n"
        f"{load_onboarding_document()}\n\n{load_agent_contract_document()}"
    )


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
    except (TimeoutError, socket.timeout) as exc:
        raise ValueError(
            f"Request to {url} timed out after {timeout:.1f}s. "
            "The configured model may still be loading."
        ) from exc
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
        return sanitize_assistant_text(value)
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return sanitize_assistant_text("\n".join(part for part in parts if part))
    return ""


def sanitize_assistant_text(text: str) -> str:
    cleaned = THINK_BLOCK_PATTERN.sub("", text)
    cleaned = CONTROL_TOKEN_PATTERN.sub("", cleaned)
    cleaned = cleaned.replace("<|im_end|>", "")
    cleaned = cleaned.replace("<|endoftext|>", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def history_to_messages(history: Optional[list[dict[str, str]]] = None) -> list[dict[str, str]]:
    extra_system_content: list[str] = []
    messages: list[dict[str, str]] = []
    for item in history or []:
        role = item.get("role")
        content = item.get("content", "").strip()
        if role not in {"user", "assistant", "system"} or not content:
            continue
        if role == "system":
            extra_system_content.append(content)
            continue
        messages.append({"role": role, "content": content})

    system_prompt = build_system_prompt()
    if extra_system_content:
        system_prompt = (
            f"{system_prompt}\n\nAdditional runtime context:\n"
            + "\n\n".join(extra_system_content)
        )

    return [{"role": "system", "content": system_prompt}, *messages]


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
            timeout=CHAT_TIMEOUT_SECONDS,
        )
        answer = extract_message_content(response.get("message", {}).get("content"))
    else:
        response = request_json(
            "POST",
            f"{config.base_url.rstrip('/')}/v1/chat/completions",
            payload={"model": config.model, "messages": messages, "temperature": 0.2},
            headers=auth_headers(config),
            timeout=CHAT_TIMEOUT_SECONDS,
        )
        choices = response.get("choices", [])
        message = choices[0].get("message", {}) if choices else {}
        answer = extract_message_content(message.get("content"))

    if not answer:
        raise ValueError("The configured LLM returned an empty response.")

    return answer
