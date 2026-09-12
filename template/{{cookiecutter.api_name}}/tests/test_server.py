"""MCP 툴 테스트 — 인프로세스 mcp.Client + respx."""

import json

import httpx
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.{{ cookiecutter.api_name_underscore }}.server import mcp


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


async def test_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == {"search_items"}
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_search_items_returns_parsed_items(base_url, sample_response):
    route = respx.get(f"{base_url}/getExampleList").mock(
        return_value=httpx.Response(200, json=sample_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("search_items", {"keyword": "예시"})

    assert route.calls.last.request.url.params["serviceKey"] == "test-key"
    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["total_count"] == 1
    assert data["items"][0]["item_name"] == "예시"


@respx.mock
async def test_api_error_is_reported_as_tool_error(base_url):
    respx.get(f"{base_url}/getExampleList").mock(
        return_value=httpx.Response(
            200,
            json={"response": {"header": {"resultCode": "30", "resultMsg": "KEY"}, "body": {}}},
        )
    )
    async with Client(mcp) as client:
        result = await client.call_tool("search_items", {})
    assert result.is_error is True
    assert "[30] KEY" in _text(result)
