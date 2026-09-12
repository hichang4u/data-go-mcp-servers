"""presidential MCP 툴 테스트."""

import json

import httpx
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.presidential_speeches.server import mcp


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


async def test_all_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == {"list_speeches", "search_speeches", "get_recent_speeches"}
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_list_speeches_2023_reshapes_rows(url_2023, page_response, rows_2023):
    respx.get(url_2023).mock(
        return_value=httpx.Response(200, json=page_response(rows_2023, per_page=2))
    )
    async with Client(mcp) as client:
        result = await client.call_tool("list_speeches", {"per_page": 2})

    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["total_count"] == 8565
    assert data["page"] == 1
    assert data["data"][1] == {
        "id": 1401097,
        "president": "문재인",
        "title": "2020 신년 합동 인사회",
        "source_url": "https://dams.pa.go.kr/dams/PUBLICATION/b.pdf",
        "location": "국내",
        "year": 2020,
    }


@respx.mock
async def test_list_speeches_2022_returns_dates(url_2022, page_response, rows_2022):
    respx.get(url_2022).mock(
        return_value=httpx.Response(200, json=page_response(rows_2022, total=7173))
    )
    async with Client(mcp) as client:
        result = await client.call_tool("list_speeches", {"use_2023_version": False})

    data = json.loads(_text(result))
    assert data["data"][0]["date"] == "1948-07-24"
    assert "year" not in data["data"][0]


@respx.mock
async def test_search_speeches_uses_server_filters_and_match_count(
    url_2023, page_response, rows_2023
):
    route = respx.get(url_2023).mock(
        return_value=httpx.Response(200, json=page_response(rows_2023[1:], match=12))
    )
    async with Client(mcp) as client:
        result = await client.call_tool("search_speeches", {"president": "문재인", "year": 2020})

    q = route.calls.last.request.url.params
    assert q["cond[대통령::EQ]"] == "문재인"
    assert q["cond[연설연도::EQ]"] == "2020"

    data = json.loads(_text(result))
    assert data["total_count"] == 12
    assert data["data"][0]["title"] == "2020 신년 합동 인사회"


@respx.mock
async def test_get_recent_speeches_reads_last_page_newest_first(
    url_2023, page_response, rows_2023
):
    calls: list[dict] = []

    def handler(request):
        calls.append(dict(request.url.params))
        if request.url.params["perPage"] == "1":
            return httpx.Response(200, json=page_response([rows_2023[0]], match=8565))
        return httpx.Response(200, json=page_response(rows_2023, page=4283, per_page=2))

    respx.get(url_2023).mock(side_effect=handler)
    async with Client(mcp) as client:
        result = await client.call_tool("get_recent_speeches", {"limit": 2})

    # 1) 건수 확인 (perPage=1) 2) 마지막 페이지 = ceil(8565 / 2) = 4283
    assert calls[0]["perPage"] == "1"
    assert calls[1] == {**calls[1], "page": "4283", "perPage": "2"}

    data = json.loads(_text(result))
    assert data["count"] == 2
    assert [s["year"] for s in data["data"]] == [2020, 1948]  # 최신순


@respx.mock
async def test_get_recent_speeches_filters_by_president(url_2023, page_response, rows_2023):
    route = respx.get(url_2023).mock(
        return_value=httpx.Response(200, json=page_response([rows_2023[1]], match=1))
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_recent_speeches", {"president": "문재인", "limit": 5})

    for call in route.calls:
        assert call.request.url.params["cond[대통령::EQ]"] == "문재인"
    data = json.loads(_text(result))
    assert data["count"] == 1
    assert data["president"] == "문재인"


@respx.mock
async def test_api_error_is_tool_error(url_2023):
    respx.get(url_2023).mock(
        return_value=httpx.Response(
            401, json={"code": -401, "msg": "유효하지 않은 인증키 입니다."}
        )
    )
    async with Client(mcp) as client:
        result = await client.call_tool("list_speeches", {})
    assert result.is_error is True
    assert "유효하지 않은 인증키" in _text(result)
