"""What an agent reads before it picks a tool: descriptions and annotations.

The annotations are advisory, but a wrong one is worse than none — a client may
auto-approve a call it was told is read-only or harmless. So every published
tool's hints are pinned here by value, read from the server the SDK builds,
not from the registry the server is built from.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

import telegram_ai_cli_mcp.ops  # noqa: F401  (registers every operation)
from telegram_ai_cli_mcp.mcp_server import _with_use_when, build_server
from telegram_ai_cli_mcp.ops._use_when import USE_WHEN
from telegram_ai_cli_mcp.opspec import REGISTRY

READ = (True, False, True, True)
LOCAL_WRITE = (False, False, False, True)
PLAN = (False, False, False, True)

# (readOnlyHint, destructiveHint, idempotentHint, openWorldHint)
EXPECTED_HINTS: dict[str, tuple[bool, bool, bool, bool]] = {
    "telegram_folders": READ,
    "telegram_chats": READ,
    "telegram_chat_read": READ,
    "telegram_chat_members": READ,
    "telegram_archive_search": READ,
    "telegram_archive_status": READ,
    "telegram_whois": READ,
    "telegram_fleet": READ,
    "telegram_inbox": READ,
    "telegram_mentions": READ,
    "telegram_message_reactions": READ,
    "telegram_drafts": READ,
    "telegram_scheduled": READ,
    "telegram_search": READ,
    "telegram_sessions": READ,
    "telegram_chat_topics": READ,
    "telegram_watch": READ,
    "telegram_archive_sync": LOCAL_WRITE,
    "telegram_media_fetch": LOCAL_WRITE,
    "telegram_media_transcribe": LOCAL_WRITE,
    # Erases a chat from the local archive: the one tool that destroys data.
    "telegram_archive_forget": (False, True, True, True),
    # A plan tool records an intention and sends nothing, so it destroys
    # nothing — even when the plan is a deletion, a ban or a leave.
    "telegram_plan_send_message": PLAN,
    "telegram_plan_reply_message": PLAN,
    "telegram_plan_send_file": PLAN,
    "telegram_plan_edit_message": PLAN,
    "telegram_plan_delete_message": PLAN,
    "telegram_plan_forward_message": PLAN,
    "telegram_plan_mark_read": PLAN,
    "telegram_plan_join_chat": PLAN,
    "telegram_plan_leave_chat": PLAN,
    "telegram_plan_create_group": PLAN,
    "telegram_plan_invite_user": PLAN,
    "telegram_plan_promote_admin": PLAN,
    "telegram_plan_ban_user": PLAN,
    "telegram_plan_unban_user": PLAN,
    "telegram_plan_kick_user": PLAN,
    "telegram_plan_restrict_user": PLAN,
    "telegram_plan_demote_admin": PLAN,
    "telegram_plan_set_profile": PLAN,
    "telegram_plan_folder_add": PLAN,
    "telegram_plan_react_message": PLAN,
    "telegram_plan_unreact_message": PLAN,
    "telegram_plan_pin_message": PLAN,
    "telegram_plan_unpin_message": PLAN,
    "telegram_plan_archive_chat": PLAN,
    "telegram_plan_mute_chat": PLAN,
    "telegram_plan_schedule_message": PLAN,
    "telegram_plan_block_user": PLAN,
    "telegram_plan_unblock_user": PLAN,
    "telegram_plan_set_chat_title": PLAN,
    "telegram_plan_set_chat_about": PLAN,
    "telegram_plan_set_chat_photo": PLAN,
}

PLAN_PARAGRAPH = "\n\nPrepares a plan and returns its id. Nothing is sent."


async def _tools() -> dict[str, Any]:
    entry = build_server().get_request_handler("tools/list")
    result = await entry.handler(None, None)
    return {tool.name: tool for tool in result.tools}


@pytest.mark.asyncio
async def test_every_tool_has_exactly_the_expected_hints() -> None:
    tools = await _tools()
    assert set(tools) == set(EXPECTED_HINTS)
    for name, tool in tools.items():
        hints = tool.annotations
        got = (
            hints.read_only_hint,
            hints.destructive_hint,
            hints.idempotent_hint,
            hints.open_world_hint,
        )
        assert got == EXPECTED_HINTS[name], f"{name}: {got}"


@pytest.mark.asyncio
async def test_use_when_is_the_second_sentence_of_every_tool() -> None:
    tools = await _tools()
    for op in REGISTRY.all():
        for plan, name in ((False, op.mcp_tool), (True, op.plan_tool)):
            if name is None:
                continue
            text = tools[name].description
            base = op.description or op.summary
            assert text.startswith(base.split(". ")[0].rstrip(".")), name
            assert USE_WHEN[op.name] in text, name
            # The selection hint comes right after the opening sentence, not
            # buried after a long operation description.
            assert text.index("Use when") < len(base.split(". ")[0]) + 3, name
            assert (PLAN_PARAGRAPH in text) is plan, name


def test_use_when_keys_are_exactly_the_published_operations() -> None:
    published = {op.name for op in REGISTRY.all() if op.mcp_tool or op.plan_tool}
    assert set(USE_WHEN) == published


@pytest.mark.asyncio
async def test_every_neighbour_named_in_a_hint_is_a_real_tool() -> None:
    tools = await _tools()
    for op_name, text in USE_WHEN.items():
        assert text.startswith("Use when "), op_name
        for neighbour in re.findall(r"\btelegram_[a-z_]+\b", text):
            assert neighbour in tools, f"{op_name} names missing tool {neighbour}"


@pytest.mark.parametrize(
    ("description", "when", "expected"),
    [
        ("Does X. More detail.", "Use when A.", "Does X. Use when A. More detail."),
        ("Ends here.", "Use when A.", "Ends here. Use when A."),
        ("No terminator", "Use when A.", "No terminator. Use when A."),
        ("Uses 3.14 today. More.", "Use when A.", "Uses 3.14 today. Use when A. More."),
        ("Is it? Yes.", "Use when A.", "Is it? Use when A. Yes."),
        ("Does X. More.", "the user asks.", "Does X. Use when the user asks. More."),
        ("Does X. More.", "  ", "Does X. More."),
        ("  Does X.  ", "Use when A.", "Does X. Use when A."),
    ],
)
def test_use_when_is_inserted_after_the_opening_sentence(
    description: str, when: str, expected: str
) -> None:
    assert _with_use_when(description, when) == expected
