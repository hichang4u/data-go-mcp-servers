"""서버 공통 유틸: configure_logging (stderr 전용), tool_errors (예외 → ToolError), READ_ONLY."""

import logging
import sys

import httpx
import pytest
from mcp import Client
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import TextContent

from data_go_mcp.core.errors import DataGoAPIError
from data_go_mcp.core.logging import configure_logging
from data_go_mcp.core.tools import READ_ONLY, tool_errors


def test_configure_logging_writes_to_stderr_only(capsys):
    configure_logging("demo")
    logging.getLogger("demo").warning("hello")

    out, err = capsys.readouterr()
    assert out == ""
    assert "hello" in err


def test_configure_logging_is_idempotent():
    configure_logging("demo")
    configure_logging("demo")
    root = logging.getLogger()
    stderr_handlers = [h for h in root.handlers if getattr(h, "stream", None) is sys.stderr]
    assert len(stderr_handlers) == 1


async def test_data_go_error_becomes_tool_error():
    with pytest.raises(ToolError, match=r"data\.go\.kr 오류 \[30\] KEY"):
        async with tool_errors():
            raise DataGoAPIError("30", "KEY")


async def test_http_status_error_becomes_tool_error():
    req = httpx.Request("GET", "https://x")
    resp = httpx.Response(502, request=req, text="bad gateway")
    with pytest.raises(ToolError, match="HTTP 502"):
        async with tool_errors():
            raise httpx.HTTPStatusError("boom", request=req, response=resp)


async def test_network_error_becomes_tool_error():
    with pytest.raises(ToolError, match="네트워크 오류"):
        async with tool_errors():
            raise httpx.ConnectError("refused")


async def test_value_error_becomes_input_tool_error():
    with pytest.raises(ToolError, match="입력값 오류: bad"):
        async with tool_errors():
            raise ValueError("bad")


async def test_tool_error_passes_through_unchanged():
    with pytest.raises(ToolError, match="^already$"):
        async with tool_errors():
            raise ToolError("already")


async def test_read_only_annotations_surface_in_list_tools():
    mcp = MCPServer("t")

    @mcp.tool(annotations=READ_ONLY)
    async def probe() -> str:
        return "x"

    (tool,) = await mcp.list_tools()
    assert tool.annotations is not None
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.open_world_hint is True


async def test_tool_error_is_reported_as_is_error_to_client():
    mcp = MCPServer("t")

    @mcp.tool()
    async def failing() -> str:
        async with tool_errors():
            raise DataGoAPIError("22", "LIMITED")

    async with Client(mcp) as client:
        result = await client.call_tool("failing", {})
    assert result.is_error is True
    (content,) = result.content
    assert isinstance(content, TextContent)
    assert "[22] LIMITED" in content.text
