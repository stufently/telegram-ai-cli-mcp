"""The default MCP surface is read-only; writing needs an explicit opt-in.

What a fresh install publishes is the claim a person relies on when they add
this server to a client without reading the configuration reference, so it is
pinned here by value rather than inferred:

* under the default ``readonly`` profile no ``telegram_plan_*`` tool is in the
  list, and calling one by name is refused before the operation runs;
* ``profile: plan`` (``TGAI_PROFILE=plan``) is the opt-in that publishes them —
  and even then no tool sends anything, which test_mcp_server asserts;
* the only non-reading tools under ``readonly`` are the four that write into
  this machine's configured directories, named one by one, so a new one has to
  be added here on purpose.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import mcp.types as types
import pytest
import yaml

import telegram_ai_cli_mcp.ops  # noqa: F401  (registers every operation)
from telegram_ai_cli_mcp import dispatch
from telegram_ai_cli_mcp.errors import ErrorCode, InvalidInput
from telegram_ai_cli_mcp.mcp_server import build_server, profile_tool_names
from telegram_ai_cli_mcp.opspec import REGISTRY, Effect

#: Every tool under `readonly` that is not a pure Telegram read. Each writes only
#: into a configured local path, checked against the client's roots.
LOCAL_WRITERS = {
    "telegram_archive_forget",
    "telegram_archive_sync",
    "telegram_media_fetch",
    "telegram_media_transcribe",
}


@pytest.fixture(autouse=True)
def _no_profile_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The environment outranks the file; a stray export would fake the default."""
    for name in [key for key in os.environ if key.startswith("TGAI_")]:
        monkeypatch.delenv(name, raising=False)


def config(tmp_path: Path, **body: Any) -> Path:
    path = tmp_path / "tgai.yaml"
    path.write_text(yaml.safe_dump(body), encoding="utf-8")
    return path


async def tools(server: Any) -> dict[str, types.Tool]:
    entry = server.get_request_handler("tools/list")
    result = await entry.handler(None, None)
    return {tool.name: tool for tool in result.tools}


async def call(server: Any, name: str, **arguments: Any) -> dict[str, Any]:
    entry = server.get_request_handler("tools/call")
    params = types.CallToolRequestParams(name=name, arguments=arguments)
    result = await entry.handler(None, params)
    return json.loads(result.content[0].text)


PLAN_TOOLS = {op.plan_tool for op in REGISTRY.plan_tools()}
READ_TOOLS = {op.mcp_tool for op in REGISTRY.read_tools()}


# -- the default ---------------------------------------------------------------


@pytest.mark.parametrize("body", [{}, {"profile": "readonly"}], ids=["unset", "explicit"])
async def test_the_default_publishes_no_plan_tool(tmp_path: Path, body: dict[str, Any]) -> None:
    published = await tools(build_server(config_path=config(tmp_path, **body)))

    assert PLAN_TOOLS, "the registry has no plan tools; this test would prove nothing"
    assert not {name for name in published if name.startswith("telegram_plan_")}
    assert set(published) == READ_TOOLS


async def test_the_default_surface_is_reads_plus_named_local_writers(tmp_path: Path) -> None:
    published = await tools(build_server(config_path=config(tmp_path)))
    by_tool = {op.mcp_tool: op for op in REGISTRY.read_tools()}

    reads = {name for name in published if by_tool[name].effect is Effect.READ}
    others = set(published) - reads

    assert others == LOCAL_WRITERS
    assert {by_tool[name].effect for name in others} == {Effect.LOCAL_WRITE}
    for name in reads:
        assert published[name].annotations.read_only_hint is True, name
    for name in others:
        assert published[name].annotations.read_only_hint is False, name


def test_no_remote_write_is_published_under_readonly() -> None:
    remote = {op.name for op in REGISTRY.all() if op.effect is Effect.REMOTE_WRITE}
    offered = profile_tool_names("readonly")

    assert remote
    for op in REGISTRY.all():
        if op.name in remote:
            assert op.mcp_tool is None and op.plan_tool not in offered, op.name


async def test_a_plan_tool_called_by_name_is_refused_before_it_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hidden from the list and closed on the call path: a name is a guessable string."""
    reached: list[str] = []

    async def spy(op: Any, *args: Any, **kwargs: Any) -> Any:
        reached.append(op.name)
        raise AssertionError("dispatch must not be reached")

    monkeypatch.setattr(dispatch, "execute", spy)
    server = build_server(config_path=config(tmp_path))

    payload = await call(server, "telegram_plan_send_message", chat="-4242", text="hi")

    assert payload["ok"] is False
    assert payload["error"]["code"] == ErrorCode.FORBIDDEN_BY_PROFILE
    assert payload["error"]["retryable"] is False
    assert "profile: plan" in payload["error"]["suggestion"]
    assert reached == []


# -- the opt-in -----------------------------------------------------------------


async def test_profile_plan_in_the_file_publishes_the_plan_tools(tmp_path: Path) -> None:
    published = await tools(build_server(config_path=config(tmp_path, profile="plan")))

    assert set(published) == READ_TOOLS | PLAN_TOOLS
    assert set(published) == set(REGISTRY.mcp_tool_names())


async def test_profile_plan_from_the_environment_publishes_them_too(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`TGAI_PROFILE=plan` is how every client block in the README opts in."""
    monkeypatch.setenv("TGAI_PROFILE", "plan")

    published = await tools(build_server(config_path=config(tmp_path, profile="readonly")))

    assert set(published) >= PLAN_TOOLS


async def test_a_plan_tool_under_plan_gets_past_the_door(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The mirror image of the refusal above, so it is not passing by accident."""
    reached: list[str] = []

    async def spy(op: Any, *args: Any, **kwargs: Any) -> Any:
        reached.append(op.name)
        raise InvalidInput("stopped by the test")

    monkeypatch.setattr(dispatch, "execute", spy)
    server = build_server(config_path=config(tmp_path, profile="plan"))

    payload = await call(server, "telegram_plan_send_message", chat="-4242", text="hi")

    assert reached == ["message.send"]
    assert payload["error"]["code"] == ErrorCode.INVALID_INPUT


# -- the gate and the profile together ---------------------------------------------


def test_naming_a_plan_tool_in_mcp_tools_under_readonly_refuses_to_start(
    tmp_path: Path,
) -> None:
    """Loud, like an unknown name: the operator expects a tool they will not get."""
    path = config(tmp_path, mcp={"tools": ["telegram_chats", "telegram_plan_send_message"]})

    with pytest.raises(InvalidInput) as caught:
        build_server(config_path=path)

    assert "telegram_plan_send_message" in caught.value.message
    assert "telegram_chats" not in caught.value.message


async def test_naming_a_plan_tool_in_mcp_tools_under_plan_publishes_it(tmp_path: Path) -> None:
    path = config(
        tmp_path,
        profile="plan",
        mcp={"tools": ["telegram_chats", "telegram_plan_send_message"]},
    )

    published = await tools(build_server(config_path=path))

    assert sorted(published) == ["telegram_chats", "telegram_plan_send_message"]
