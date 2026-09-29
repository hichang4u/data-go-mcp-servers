"""bok-ecos MCP 툴 테스트."""

import json

import httpx
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.bok_ecos.server import mcp

from .conftest import ERROR_KEY, ERROR_NO_DATA


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


async def test_all_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == {
        "find_statistic_table",
        "get_statistic_items",
        "get_statistic_data",
        "get_key_statistics",
        "search_term",
    }
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_find_statistic_table_returns_codes_for_a_keyword(base_url, table_list):
    respx.get(url__startswith=f"{base_url}/StatisticTableList").mock(
        return_value=httpx.Response(200, json=table_list)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("find_statistic_table", {"keyword": "기준금리"})

    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["items"][0]["stat_code"] == "722Y001"
    assert data["items"][0]["cycle"] == "M"


@respx.mock
async def test_get_statistic_items_lists_periods_per_cycle(base_url, item_list):
    respx.get(url__startswith=f"{base_url}/StatisticItemList").mock(
        return_value=httpx.Response(200, json=item_list)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_statistic_items", {"stat_code": "722Y001"})

    data = json.loads(_text(result))
    cycles = {i["cycle"]: (i["start_time"], i["end_time"]) for i in data["items"]}
    assert cycles["M"] == ("199901", "202609")
    assert cycles["A"] == ("1999", "2025")


@respx.mock
async def test_get_statistic_data_returns_time_series(base_url, search_result):
    route = respx.get(url__startswith=f"{base_url}/StatisticSearch").mock(
        return_value=httpx.Response(200, json=search_result)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_statistic_data",
            {
                "stat_code": "722Y001",
                "cycle": "M",
                "start_time": "202401",
                "end_time": "202403",
                "item_code1": "0101000",
            },
        )

    assert str(route.calls.last.request.url).endswith("/722Y001/M/202401/202403/0101000")
    data = json.loads(_text(result))
    assert data["total_count"] == 27
    assert data["items"][0]["time"] == "202401"
    assert data["items"][0]["value"] == 3.5
    assert data["items"][0]["unit_name"] == "연%"


@respx.mock
async def test_get_statistic_data_without_item_code_returns_every_item(base_url, search_result):
    route = respx.get(url__startswith=f"{base_url}/StatisticSearch").mock(
        return_value=httpx.Response(200, json=search_result)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_statistic_data",
            {
                "stat_code": "722Y001",
                "cycle": "M",
                "start_time": "202401",
                "end_time": "202403",
            },
        )

    assert str(route.calls.last.request.url).endswith("/202401/202403")
    assert json.loads(_text(result))["total_count"] == 27


@respx.mock
async def test_get_statistic_data_empty_period_is_not_an_error(base_url):
    respx.get(url__startswith=f"{base_url}/StatisticSearch").mock(
        return_value=httpx.Response(200, json=ERROR_NO_DATA)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_statistic_data",
            {
                "stat_code": "722Y001",
                "cycle": "M",
                "start_time": "209901",
                "end_time": "209912",
            },
        )

    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["items"] == [] and data["total_count"] == 0


@respx.mock
async def test_get_key_statistics_filters_by_class(base_url, key_statistics):
    respx.get(url__startswith=f"{base_url}/KeyStatisticList").mock(
        return_value=httpx.Response(200, json=key_statistics)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_key_statistics", {"class_name": "금리"})

    data = json.loads(_text(result))
    assert [i["name"] for i in data["items"]] == ["한국은행 기준금리"]
    assert data["items"][0]["value"] == 2.5


@respx.mock
async def test_search_term_explains_a_word(base_url, word):
    respx.get(url__startswith=f"{base_url}/StatisticWord").mock(
        return_value=httpx.Response(200, json=word)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("search_term", {"word": "기준금리"})

    data = json.loads(_text(result))
    assert data["items"][0]["word"] == "기준금리"
    assert "정책금리" in data["items"][0]["content"]


async def test_bad_cycle_is_input_error():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_statistic_data",
            {
                "stat_code": "722Y001",
                "cycle": "X",
                "start_time": "202401",
                "end_time": "202403",
            },
        )
    assert result.is_error is True
    assert "입력값 오류" in _text(result)


@respx.mock
async def test_api_error_is_tool_error(base_url):
    respx.get(url__startswith=f"{base_url}/StatisticSearch").mock(
        return_value=httpx.Response(200, json=ERROR_KEY)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_statistic_data",
            {
                "stat_code": "722Y001",
                "cycle": "M",
                "start_time": "202401",
                "end_time": "202403",
            },
        )

    assert result.is_error is True
    assert "한국은행 ECOS 오류 [INFO-100]" in _text(result)


@respx.mock
async def test_get_key_statistics_asks_for_more_than_the_list_size(base_url, key_statistics):
    """100대 지표는 실제로 101건이다 — 기본값이 100이면 한 건이 잘린다 (2026-09-29 실호출)."""
    route = respx.get(url__startswith=f"{base_url}/KeyStatisticList").mock(
        return_value=httpx.Response(200, json=key_statistics)
    )
    async with Client(mcp) as client:
        await client.call_tool("get_key_statistics", {})

    end = int(str(route.calls.last.request.url).rstrip("/").split("/")[-1])
    assert end >= 101
