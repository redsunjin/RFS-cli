from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from rfs_cli.config import load_index, load_shell_memory, resolve_state_dir
from rfs_cli.models import AppConfig, GuidanceResponse, UserIntent

SEARCH_KEYWORDS = ["search", "find", "lookup", "검색", "찾", "조회"]
SETUP_KEYWORDS = ["index", "connect", "setup", "start", "설정", "연결", "시작"]
ADD_SOURCE_KEYWORDS = ["add", "register", "등록", "추가", "연결"]
INSPECT_KEYWORDS = ["show", "open", "inspect", "문서", "파일", "노트", "보여", "열어"]
DIAGNOSE_KEYWORDS = ["doctor", "status", "diagnose", "check", "진단", "상태", "점검", "확인"]
LIST_SOURCE_KEYWORDS = ["source", "sources", "목록", "리스트", "등록된", "연결된"]
REPEAT_RECENT_KEYWORDS = ["recent", "last", "again", "방금", "최근", "다시", "이전", "아까"]
SOURCE_KIND_KEYWORDS = ["obsidian", "local", "vault", "볼트", "폴더", "folder", "directory"]
OBSIDIAN_KEYWORDS = ["obsidian", "vault", "볼트"]
LOCAL_KEYWORDS = ["local", "folder", "directory", "폴더"]
RECENT_KEYWORDS = ["recent", "last", "again", "방금", "최근", "다시", "이전"]
AMBIGUOUS_ASK_STOPWORDS = {
    "a",
    "add",
    "again",
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
    "inspect",
    "lookup",
    "notes",
    "open",
    "query",
    "recent",
    "register",
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
    "방금",
    "보여",
    "상태",
    "시작",
    "싶어",
    "어떻게",
    "어케",
    "열어",
    "이전",
    "조회",
    "점검",
    "최근",
    "찾",
    "찾고",
    "찾기",
    "파일",
    "해",
    "확인",
}
PATH_TOKEN_PATTERN = re.compile(r"([~/][^\s\"']+|[A-Za-z]:\\[^\s\"']+)")


def contains_path_hint(text: str) -> bool:
    return any(token in text for token in ["/", "\\", "~", ".md", ".txt", ":\\"])


def extract_path_hint(text: str) -> Optional[str]:
    quoted_matches = re.findall(r'["\']([^"\']+)["\']', text)
    for value in quoted_matches:
        if contains_path_hint(value):
            return value

    match = PATH_TOKEN_PATTERN.search(text)
    if match is not None:
        return match.group(1)
    return None


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
        "줘",
    ]
    for suffix in suffixes:
        if normalized.endswith(suffix) and len(normalized) > len(suffix) + 1:
            return normalized[: -len(suffix)]
    return normalized


def meaningful_guidance_terms(question: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9가-힣_-]+", question.lower())
    normalized_tokens = [normalize_guidance_token(token) for token in tokens]
    return [token for token in normalized_tokens if token not in AMBIGUOUS_ASK_STOPWORDS]


def extract_source_type(lowered: str) -> Optional[str]:
    if any(keyword in lowered for keyword in OBSIDIAN_KEYWORDS):
        return "obsidian"
    if any(keyword in lowered for keyword in LOCAL_KEYWORDS):
        return "local"
    return None


def extract_file_type_hint(lowered: str) -> Optional[str]:
    if any(keyword in lowered for keyword in ["markdown", ".md", "md "]):
        return "md"
    if any(keyword in lowered for keyword in ["text", ".txt", "txt "]):
        return "txt"
    return None


def extract_recent_tool_command(state_dir: Path) -> Optional[str]:
    try:
        memory = load_shell_memory(state_dir=resolve_state_dir(state_dir))
    except ValueError:
        return None

    if memory is None:
        return None

    for event in reversed(memory.events):
        if event.kind == "tool":
            if event.metadata.get("tool_type") == "external":
                continue
            command = event.metadata.get("command")
            if isinstance(command, str) and command:
                return command
    return None


def format_recent_command(command: str) -> str:
    normalized = command.strip()
    if normalized.startswith("rfs "):
        return normalized
    first_token = normalized.split(" ", 1)[0]
    if first_token in {
        "version",
        "doctor",
        "init",
        "ask",
        "search",
        "show",
        "index",
        "dev",
        "agent",
        "drive",
        "llm",
        "research",
    }:
        return f"rfs {normalized}"
    return normalized


def classify_command_action_type(command: str) -> str:
    normalized = command.removeprefix("rfs ").strip()
    if normalized.startswith("index add"):
        return "state-changing"
    if normalized.startswith("index run"):
        return "state-changing"
    if normalized.startswith("init"):
        return "state-changing"
    if normalized.startswith("llm setup"):
        return "state-changing"
    if normalized.startswith("drive auth"):
        return "state-changing"
    if normalized.startswith("research export"):
        return "state-changing"
    return "read-only"


def is_source_listing_request(lowered: str) -> bool:
    has_source_keyword = any(keyword in lowered for keyword in LIST_SOURCE_KEYWORDS)
    has_listing_intent = any(
        keyword in lowered for keyword in ["list", "show", "what", "뭐", "무엇", "보여", "알려"]
    )
    return has_source_keyword and has_listing_intent


def is_recent_repeat_request(lowered: str) -> bool:
    has_recent_keyword = any(keyword in lowered for keyword in REPEAT_RECENT_KEYWORDS)
    has_repeat_intent = any(
        keyword in lowered for keyword in ["repeat", "rerun", "retry", "다시", "재실행", "다시해"]
    )
    has_recall_intent = any(
        keyword in lowered for keyword in ["뭐", "무엇", "what", "recent", "last", "방금", "최근"]
    )
    return has_recent_keyword and (has_repeat_intent or has_recall_intent)


def detect_guidance_goal(lowered: str, source_type: Optional[str], path_hint: Optional[str]) -> str:
    if is_recent_repeat_request(lowered):
        return "repeat_recent"
    if is_source_listing_request(lowered):
        return "list_sources"
    if any(keyword in lowered for keyword in DIAGNOSE_KEYWORDS):
        return "diagnose"
    if (
        source_type is not None or path_hint is not None
    ) and any(keyword in lowered for keyword in SETUP_KEYWORDS + ADD_SOURCE_KEYWORDS):
        return "add_source"
    if any(keyword in lowered for keyword in INSPECT_KEYWORDS):
        return "inspect"
    if any(keyword in lowered for keyword in SEARCH_KEYWORDS):
        return "search"
    if any(keyword in lowered for keyword in SETUP_KEYWORDS):
        return "setup"
    return "unknown"


def interpret_user_intent(question: str) -> UserIntent:
    lowered = question.lower()
    meaningful_terms = meaningful_guidance_terms(question)
    path_hint = extract_path_hint(question)
    source_type = extract_source_type(lowered)
    file_type = extract_file_type_hint(lowered)
    goal = detect_guidance_goal(lowered, source_type, path_hint)
    missing_fields: list[str] = []

    if goal == "add_source":
        if source_type is None:
            missing_fields.append("source_type")
        if path_hint is None:
            missing_fields.append("source_path")
    elif goal in {"search", "setup"} and not source_type and not path_hint and not meaningful_terms:
        missing_fields.append("source_or_path")
    elif goal == "inspect" and not path_hint and not meaningful_terms:
        missing_fields.append("document_target")

    confidence = 0.92 if goal != "unknown" else 0.4
    return UserIntent(
        goal=goal,
        entities={
            "source_type": source_type,
            "path_hint": path_hint,
            "file_type": file_type,
            "meaningful_terms": meaningful_terms,
            "wants_recent_context": any(keyword in lowered for keyword in RECENT_KEYWORDS),
        },
        missing_fields=missing_fields,
        confidence=confidence,
    )


def format_search_command(
    query_terms: list[str],
    enabled_sources: list,
    file_type: Optional[str],
) -> str:
    query = " ".join(query_terms[:6]) if query_terms else "<query>"
    command = f'rfs search "{query}"'
    if len(enabled_sources) == 1:
        command = f"{command} --source-id {enabled_sources[0].id}"
    if file_type is not None:
        command = f"{command} --file-type {file_type}"
    return command


def plan_guidance_response(
    question: str,
    app_config: AppConfig,
    state_dir: Path,
) -> Optional[GuidanceResponse]:
    intent = interpret_user_intent(question)
    enabled_sources = [source for source in app_config.sources if source.enabled]
    resolved_state_dir = resolve_state_dir(state_dir)
    recent_command = extract_recent_tool_command(resolved_state_dir)

    index_store = None
    index_invalid = False
    shell_memory_invalid = False
    try:
        index_store = load_index(state_dir=resolved_state_dir)
    except ValueError:
        index_invalid = True

    try:
        load_shell_memory(state_dir=resolved_state_dir)
    except ValueError:
        shell_memory_invalid = True

    if index_invalid or shell_memory_invalid:
        problems: list[str] = []
        if index_invalid:
            problems.append("index 상태")
        if shell_memory_invalid:
            problems.append("shell memory 상태")
        return GuidanceResponse(
            summary=(
                f"{', '.join(problems)}를 먼저 점검하는 편이 안전합니다."
            ),
            recommended_command="rfs doctor --verbose",
            next_step="rfs doctor --verbose",
            action_type="read-only",
        )

    if intent.goal == "repeat_recent":
        if recent_command is None:
            return GuidanceResponse(
                summary="",
                follow_up_question=(
                    "최근 실행 기록이 아직 없습니다. "
                    "대신 어떤 작업을 다시 하고 싶은지 한 줄로 알려주세요."
                ),
            )
        formatted_command = format_recent_command(recent_command)
        return GuidanceResponse(
            summary=(
                f"가장 최근에 실행한 내부 명령은 `{recent_command}`였습니다. "
                "같은 흐름을 다시 보려면 아래 명령을 쓰면 됩니다."
            ),
            recommended_command=formatted_command,
            next_step=formatted_command,
            action_type=classify_command_action_type(formatted_command),
        )

    if intent.goal == "list_sources":
        if enabled_sources:
            return GuidanceResponse(
                summary="현재 연결된 source 목록을 바로 확인할 수 있습니다.",
                recommended_command="rfs index sources",
                next_step="rfs index sources",
                action_type="read-only",
            )
        return GuidanceResponse(
            summary="아직 등록된 source가 없으므로 먼저 하나를 연결해야 합니다.",
            recommended_command='rfs ask "옵시디언 볼트를 추가하려면?"',
            next_step='rfs ask "옵시디언 볼트를 추가하려면?"',
            action_type="read-only",
        )

    if not enabled_sources and intent.goal in {"search", "setup"}:
        if "source_or_path" in intent.missing_fields:
            return GuidanceResponse(
                summary="",
                follow_up_question=(
                    "어떤 경로를 먼저 연결할까요? local 폴더인지 Obsidian vault인지와 "
                    "경로를 한 줄로 알려주세요."
                ),
            )

    if intent.goal == "add_source":
        source_type = intent.entities["source_type"]
        path_hint = intent.entities["path_hint"]
        if source_type is None and path_hint is not None:
            return GuidanceResponse(
                summary="",
                follow_up_question="그 경로를 local로 볼까요, Obsidian vault로 볼까요?",
            )
        if source_type is not None and path_hint is None:
            label = "Obsidian vault" if source_type == "obsidian" else "local 폴더"
            return GuidanceResponse(
                summary="",
                follow_up_question=f"{label} 경로를 한 줄로 알려주세요.",
            )
        if source_type is not None and path_hint is not None:
            return GuidanceResponse(
                summary="경로와 source 종류가 보이므로 바로 등록할 수 있습니다.",
                recommended_command=f'rfs index add "{path_hint}" --source {source_type}',
                next_step=f'rfs index add "{path_hint}" --source {source_type}',
                action_type="state-changing",
            )

    if len(enabled_sources) > 1 and index_store is None and intent.goal == "search":
        source_ids = [source.id for source in enabled_sources]
        lowered = question.lower()
        if not any(source_id.lower() in lowered for source_id in source_ids):
            return GuidanceResponse(
                summary="",
                follow_up_question=(
                    "어느 source부터 인덱싱할까요? "
                    f"{', '.join(source_ids)} 중 하나를 알려주세요."
                ),
            )

    if enabled_sources and index_store is None and intent.goal in {"search", "inspect"}:
        return GuidanceResponse(
            summary="등록된 source는 있지만 인덱스가 아직 없어서, 먼저 인덱스를 만들어야 합니다.",
            recommended_command="rfs index run",
            next_step="rfs index run",
            action_type="state-changing",
        )

    if intent.goal == "diagnose":
        summary = "현재 상태를 점검하려면 진단 명령부터 실행하는 편이 가장 안전합니다."
        if recent_command is not None:
            summary = (
                f"최근 실행 명령은 `{recent_command}`였습니다. "
                "전체 상태를 점검하려면 진단 명령부터 보는 편이 좋습니다."
            )
        return GuidanceResponse(
            summary=summary,
            recommended_command="rfs doctor --verbose",
            next_step="rfs doctor --verbose",
            action_type="read-only",
        )

    if index_store is not None and intent.goal == "search":
        query_terms = intent.entities["meaningful_terms"]
        if query_terms:
            return GuidanceResponse(
                summary="이미 인덱스가 있으므로 바로 검색해도 됩니다.",
                recommended_command=format_search_command(
                    query_terms,
                    enabled_sources,
                    intent.entities["file_type"],
                ),
                next_step=format_search_command(
                    query_terms,
                    enabled_sources,
                    intent.entities["file_type"],
                ),
                action_type="read-only",
            )

    if index_store is not None and intent.goal == "inspect":
        path_hint = intent.entities["path_hint"]
        query_terms = intent.entities["meaningful_terms"]
        if path_hint is not None:
            return GuidanceResponse(
                summary="대상 경로가 보이므로 바로 열어볼 수 있습니다.",
                recommended_command=f'rfs show "{path_hint}"',
                next_step=f'rfs show "{path_hint}"',
                action_type="read-only",
            )
        if query_terms:
            search_command = format_search_command(
                query_terms,
                enabled_sources,
                intent.entities["file_type"],
            )
            return GuidanceResponse(
                summary="먼저 검색으로 후보를 좁힌 다음 `show`로 여는 편이 안전합니다.",
                recommended_command=search_command,
                next_step=search_command,
                action_type="read-only",
            )
        return GuidanceResponse(
            summary="",
            follow_up_question=(
                "어떤 문서를 열어볼까요? 경로, 문서 ID, 또는 검색어를 한 줄로 알려주세요."
            ),
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

    action_label = ""
    if response.action_type == "read-only":
        action_label = "읽기 전용"
    elif response.action_type == "state-changing":
        action_label = "상태 변경"

    if response.summary:
        if action_label:
            return f"{response.summary}\n권장 명령 ({action_label}): `{command}`"
        return f"{response.summary}\n권장 명령: `{command}`"
    if action_label:
        return f"권장 명령 ({action_label}): `{command}`"
    return f"권장 명령: `{command}`"
