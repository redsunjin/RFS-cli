from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from rfs_cli.config import load_index, resolve_state_dir
from rfs_cli.models import (
    AppConfig,
    CommandSuggestion,
    GuidanceResponse,
    ShellMemory,
    SourceConfig,
    UserIntent,
)

AMBIGUOUS_ASK_STOPWORDS = {
    "a",
    "add",
    "and",
    "connect",
    "do",
    "find",
    "for",
    "get",
    "hae",
    "how",
    "i",
    "index",
    "lookup",
    "notes",
    "query",
    "search",
    "setup",
    "show",
    "start",
    "the",
    "to",
    "use",
    "what",
    "검색",
    "문서",
    "방법",
    "보여",
    "시작",
    "어떻게",
    "어케",
    "열어",
    "조회",
    "찾",
    "찾기",
    "파일",
    "해",
}


def format_source_summary(sources: list[SourceConfig]) -> list[str]:
    if not sources:
        return ["Configured sources: none."]

    lines = [f"Configured sources: {len(sources)}"]
    for source in sources[:8]:
        status = "enabled" if source.enabled else "disabled"
        lines.append(f"- {source.id} [{source.type}] {status} root={source.root_path}")
    if len(sources) > 8:
        lines.append(f"- ... {len(sources) - 8} more source(s)")
    return lines


def build_guidance_runtime_context(app_config: AppConfig, state_dir: Path) -> list[dict[str, str]]:
    resolved_state_dir = resolve_state_dir(state_dir)
    lines = [
        "Workspace guidance context:",
        f"- state_dir: {resolved_state_dir}",
        *format_source_summary(app_config.sources),
    ]

    try:
        index_store = load_index(state_dir=resolved_state_dir)
    except ValueError as exc:
        lines.append("- index_status: invalid")
        lines.append(f"- index_error: {exc}")
        lines.append(
            "- guidance_hint: recommend rebuilding the index with `rfs index run` "
            "after checking configured sources."
        )
        return [{"role": "system", "content": "\n".join(lines)}]

    if index_store is None:
        lines.append("- index_status: missing")
        if app_config.sources:
            lines.append(
                "- guidance_hint: sources exist, so prefer `rfs index run` before "
                "recommending `search` or `show`."
            )
        else:
            lines.append(
                "- guidance_hint: no sources exist, so prefer `rfs index add <root> "
                "--source local|obsidian` before `rfs index run`."
            )
        return [{"role": "system", "content": "\n".join(lines)}]

    source_ids = sorted({document.source_id for document in index_store.documents})
    file_types = sorted({document.file_type for document in index_store.documents})
    lines.extend(
        [
            "- index_status: available",
            f"- indexed_document_count: {len(index_store.documents)}",
            f"- indexed_source_ids: {', '.join(source_ids) if source_ids else 'none'}",
            f"- indexed_file_types: {', '.join(file_types[:10]) if file_types else 'none'}",
            "- guidance_hint: prefer grounded `search`, `show`, and filter suggestions "
            "that match the available sources and indexed content.",
        ]
    )
    return [{"role": "system", "content": "\n".join(lines)}]


def contains_path_hint(text: str) -> bool:
    return any(token in text for token in ["/", "\\", "~", ".md", ".txt", ":\\"])


def normalize_guidance_token(token: str) -> str:
    normalized = token.lower()
    suffixes = [
        "하려면",
        "하려",
        "하면",
        "하기",
        "하고",
        "에서",
        "으로",
        "부터",
        "까지",
        "처럼",
        "한줄",
        "은",
        "는",
        "이",
        "가",
        "을",
        "를",
        "에",
        "와",
        "과",
        "도",
        "만",
        "요",
    ]
    for suffix in suffixes:
        if normalized.endswith(suffix) and len(normalized) > len(suffix) + 1:
            normalized = normalized[: -len(suffix)]
            break
    return normalized


def meaningful_guidance_terms(question: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9가-힣_-]+", question.lower())
    normalized_tokens = [normalize_guidance_token(token) for token in tokens]
    return [token for token in normalized_tokens if token not in AMBIGUOUS_ASK_STOPWORDS]


def detect_source_hint(lowered_question: str) -> Optional[str]:
    if any(keyword in lowered_question for keyword in ["obsidian", "vault", "볼트"]):
        return "obsidian"
    if any(keyword in lowered_question for keyword in ["local", "폴더", "folder", "directory"]):
        return "local"
    return None


def interpret_user_intent(question: str) -> UserIntent:
    lowered = question.lower()
    meaningful_terms = meaningful_guidance_terms(question)
    requested_path_hint = contains_path_hint(question)
    requested_source_hint = detect_source_hint(lowered)

    wants_search = any(
        keyword in lowered for keyword in ["search", "find", "lookup", "검색", "찾", "조회"]
    )
    wants_setup = any(
        keyword in lowered
        for keyword in ["index", "add", "connect", "setup", "start", "등록", "추가", "연결", "설정"]
    )
    wants_inspect = any(
        keyword in lowered for keyword in ["show", "open", "문서", "파일", "노트", "보여", "열어"]
    )
    wants_diagnose = any(
        keyword in lowered for keyword in ["doctor", "diagnose", "status", "문제", "진단", "상태"]
    )

    goal = "unknown"
    confidence = 0.35
    if wants_inspect:
        goal = "inspect"
        confidence = 0.9
    elif wants_search:
        goal = "search"
        confidence = 0.85
    elif wants_setup:
        goal = "setup"
        confidence = 0.75
    elif wants_diagnose:
        goal = "diagnose"
        confidence = 0.8

    missing_fields: list[str] = []
    if goal == "inspect" and not requested_path_hint:
        missing_fields.append("target")

    return UserIntent(
        goal=goal,
        entities={
            "question": question,
            "question_lower": lowered,
            "meaningful_terms": meaningful_terms,
            "requested_source_hint": requested_source_hint,
            "requested_path_hint": requested_path_hint,
            "wants_search": wants_search,
            "wants_setup": wants_setup,
            "wants_inspect": wants_inspect,
            "wants_diagnose": wants_diagnose,
        },
        missing_fields=missing_fields,
        confidence=confidence,
    )


def plan_command_suggestion(
    intent: UserIntent,
    app_config: AppConfig,
    state_dir: Path,
) -> CommandSuggestion:
    resolved_state_dir = resolve_state_dir(state_dir)
    enabled_sources = [source for source in app_config.sources if source.enabled]
    lowered_question = str(intent.entities.get("question_lower", ""))
    meaningful_terms = list(intent.entities.get("meaningful_terms", []))
    requested_source_hint = intent.entities.get("requested_source_hint")
    requested_path_hint = bool(intent.entities.get("requested_path_hint"))

    try:
        index_store = load_index(state_dir=resolved_state_dir)
    except ValueError:
        index_store = None

    if not enabled_sources and intent.goal in {"search", "setup"}:
        if not requested_source_hint and not requested_path_hint and not meaningful_terms:
            return CommandSuggestion(
                command=None,
                reason="Need a source kind and path before suggesting indexing.",
                mode="follow_up",
                missing_state=["source_kind", "path"],
            )

    if len(enabled_sources) > 1 and index_store is None and intent.goal == "search":
        source_ids = [source.id for source in enabled_sources]
        if not any(source_id.lower() in lowered_question for source_id in source_ids):
            return CommandSuggestion(
                command=None,
                reason="Need a source selection before recommending indexing.",
                mode="follow_up",
                missing_state=["source_id"],
            )

    if index_store is not None and intent.goal == "inspect":
        has_document_id_hint = any(
            document.document_id in lowered_question for document in index_store.documents[:20]
        )
        if not requested_path_hint and not has_document_id_hint:
            return CommandSuggestion(
                command=None,
                reason="Need a document target before recommending `show`.",
                mode="follow_up",
                missing_state=["target"],
            )

    if intent.goal == "search":
        if index_store is None and enabled_sources:
            return CommandSuggestion(
                command="rfs index run",
                reason="Sources exist but the index is not ready yet.",
                mode="write",
                missing_state=["index"],
            )
        if index_store is None:
            return CommandSuggestion(
                command="rfs index add <root> --source local|obsidian",
                reason="A source must be configured before search can work.",
                mode="write",
                missing_state=["source"],
            )
        return CommandSuggestion(
            command="rfs search <query>",
            reason="Indexed search is available for this request.",
            mode="read",
            missing_state=[],
        )

    if intent.goal == "inspect":
        return CommandSuggestion(
            command="rfs show <document-id-or-path>",
            reason="Indexed inspection is available when a target is known.",
            mode="read",
            missing_state=[],
        )

    if intent.goal == "diagnose":
        return CommandSuggestion(
            command="rfs doctor --verbose",
            reason="Diagnostics are the safest grounded next step.",
            mode="read",
            missing_state=[],
        )

    if intent.goal == "setup":
        if enabled_sources:
            return CommandSuggestion(
                command="rfs index run",
                reason="Configured sources should be indexed next.",
                mode="write",
                missing_state=[],
            )
        return CommandSuggestion(
            command="rfs index add <root> --source local|obsidian",
            reason="A source needs to be configured first.",
            mode="write",
            missing_state=["source"],
        )

    return CommandSuggestion(
        command=None,
        reason="No deterministic guidance override is required.",
        mode="read",
        missing_state=[],
    )


def render_guidance_response(
    intent: UserIntent,
    suggestion: CommandSuggestion,
    app_config: AppConfig,
    state_dir: Path,
) -> Optional[GuidanceResponse]:
    del intent
    del state_dir

    if suggestion.mode == "follow_up":
        if suggestion.missing_state == ["source_id"]:
            enabled_source_ids = [source.id for source in app_config.sources if source.enabled]
            question = (
                "어느 source부터 인덱싱할까요? "
                f"{', '.join(enabled_source_ids)} 중 하나를 알려주세요."
            )
        elif "target" in suggestion.missing_state:
            question = "어떤 문서를 열어볼까요? 경로, 문서 ID, 또는 검색어를 한 줄로 알려주세요."
        else:
            question = (
                "어떤 경로를 먼저 연결할까요? local 폴더인지 Obsidian vault인지와 "
                "경로를 한 줄로 알려주세요."
            )

        return GuidanceResponse(
            summary=question,
            recommended_command=None,
            next_step=question,
            alternatives=[],
        )

    return None


def shell_history_messages(
    memory: ShellMemory,
    limit: int = 8,
    include_latest: bool = True,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are answering from inside an already active `rfs shell` session. "
                "The user is already in the shell right now. "
                "Do not tell the user to run `rfs shell` unless they are explicitly "
                "asking how to start a new session."
            ),
        }
    ]
    events = memory.events if include_latest else memory.events[:-1]
    for event in events[-limit:]:
        if event.kind == "user":
            messages.append({"role": "user", "content": event.content})
            continue
        if event.kind == "assistant":
            messages.append({"role": "assistant", "content": event.content})
            continue
        if event.kind == "tool":
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Recent tool execution:\n"
                        f'command: {event.metadata.get("command", "unknown")}\n'
                        f"output:\n{event.content}"
                    ),
                }
            )
    return messages


def build_shell_guidance_history(
    app_config: AppConfig,
    state_dir: Path,
    memory: ShellMemory,
) -> list[dict[str, str]]:
    return build_guidance_runtime_context(app_config, state_dir) + shell_history_messages(
        memory,
        include_latest=False,
    )
