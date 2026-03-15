from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from rfs_cli.config import load_index, resolve_state_dir
from rfs_cli.models import AppConfig, CommandSuggestion, GuidanceResponse, UserIntent

SEARCH_KEYWORDS = ["search", "find", "lookup", "검색", "찾", "조회"]
SETUP_KEYWORDS = ["index", "add", "connect", "setup", "start", "등록", "추가", "연결", "설정"]
SHOW_KEYWORDS = ["show", "open", "문서", "파일", "노트", "보여", "열어"]
DIAGNOSE_KEYWORDS = ["doctor", "status", "diagnose", "check", "진단", "상태", "점검", "확인"]
SOURCE_KIND_KEYWORDS = ["obsidian", "local", "vault", "볼트", "폴더", "folder", "directory"]
AMBIGUOUS_ASK_STOPWORDS = {
    "a",
    "add",
    "and",
    "check",
    "connect",
    "do",
    "doctor",
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
    "status",
    "the",
    "to",
    "use",
    "what",
    "검색",
    "문서",
    "방법",
    "보여",
    "상태",
    "시작",
    "어떻게",
    "어케",
    "열어",
    "조회",
    "점검",
    "찾",
    "찾기",
    "파일",
    "해",
    "확인",
}


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
            return normalized[: -len(suffix)]
    return normalized


def meaningful_guidance_terms(question: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9가-힣_-]+", question.lower())
    normalized_tokens = [normalize_guidance_token(token) for token in tokens]
    return [token for token in normalized_tokens if token not in AMBIGUOUS_ASK_STOPWORDS]


def detect_guidance_goal(lowered: str) -> str:
    if any(keyword in lowered for keyword in DIAGNOSE_KEYWORDS):
        return "diagnose"
    if any(keyword in lowered for keyword in SHOW_KEYWORDS):
        return "show"
    if any(keyword in lowered for keyword in SEARCH_KEYWORDS):
        return "search"
    if any(keyword in lowered for keyword in SETUP_KEYWORDS):
        return "setup"
    return "unknown"


def interpret_user_intent(question: str) -> UserIntent:
    lowered = question.lower()
    meaningful_terms = meaningful_guidance_terms(question)
    goal = detect_guidance_goal(lowered)
    mentions_source_kind = any(keyword in lowered for keyword in SOURCE_KIND_KEYWORDS)
    path_hint = contains_path_hint(question)
    missing_fields: list[str] = []

    if (
        goal in {"search", "setup"}
        and not mentions_source_kind
        and not path_hint
        and not meaningful_terms
    ):
        missing_fields.append("source_or_path")
    if goal == "show" and not path_hint:
        missing_fields.append("document_target")

    confidence = 0.9 if goal != "unknown" else 0.4
    return UserIntent(
        goal=goal,
        entities={
            "mentions_source_kind": mentions_source_kind,
            "path_hint": path_hint,
            "meaningful_terms": meaningful_terms,
        },
        missing_fields=missing_fields,
        confidence=confidence,
    )


def plan_guidance_response(
    question: str,
    app_config: AppConfig,
    state_dir: Path,
) -> Optional[GuidanceResponse]:
    intent = interpret_user_intent(question)
    lowered = question.lower()
    enabled_sources = [source for source in app_config.sources if source.enabled]

    try:
        index_store = load_index(state_dir=resolve_state_dir(state_dir))
    except ValueError:
        index_store = None

    if not enabled_sources and intent.goal in {"search", "setup"}:
        if "source_or_path" in intent.missing_fields:
            return GuidanceResponse(
                summary="",
                follow_up_question=(
                    "어떤 경로를 먼저 연결할까요? local 폴더인지 Obsidian vault인지와 "
                    "경로를 한 줄로 알려주세요."
                ),
            )

    if len(enabled_sources) > 1 and index_store is None and intent.goal == "search":
        source_ids = [source.id for source in enabled_sources]
        if not any(source_id.lower() in lowered for source_id in source_ids):
            return GuidanceResponse(
                summary="",
                follow_up_question=(
                    "어느 source부터 인덱싱할까요? "
                    f"{', '.join(source_ids)} 중 하나를 알려주세요."
                ),
            )

    if index_store is not None and intent.goal == "show":
        has_target_hint = intent.entities["path_hint"] or any(
            document.document_id in question for document in index_store.documents[:20]
        )
        if not has_target_hint:
            return GuidanceResponse(
                summary="",
                follow_up_question=(
                    "어떤 문서를 열어볼까요? 경로, 문서 ID, 또는 검색어를 한 줄로 알려주세요."
                ),
            )

    suggestion = plan_command_suggestion(intent, enabled_sources, index_store)
    if suggestion is None:
        return None

    return GuidanceResponse(
        summary=suggestion.reason,
        recommended_command=suggestion.command,
        next_step=suggestion.command,
    )


def plan_command_suggestion(
    intent: UserIntent,
    enabled_sources: list,
    index_store,
) -> Optional[CommandSuggestion]:
    if intent.goal == "diagnose":
        return CommandSuggestion(
            command="rfs doctor --verbose",
            reason="현재 상태를 점검하려면 진단 명령부터 실행하는 편이 가장 안전합니다.",
        )

    if enabled_sources and index_store is None and intent.goal in {"search", "show"}:
        return CommandSuggestion(
            command="rfs index run",
            reason="등록된 source는 있지만 인덱스가 아직 없어서, 먼저 인덱스를 만들어야 합니다.",
            missing_state=["index"],
        )

    return None


def render_guidance_response(response: GuidanceResponse, shell_mode: bool = False) -> str:
    if response.follow_up_question is not None:
        return response.follow_up_question

    if response.recommended_command is None:
        return response.summary

    command = response.recommended_command
    if shell_mode and command.startswith("rfs "):
        command = command[4:]

    if response.summary:
        return f"{response.summary}\n권장 명령: `{command}`"
    return f"권장 명령: `{command}`"
