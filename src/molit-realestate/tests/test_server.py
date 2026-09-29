"""molit MCP 툴 테스트."""

import json

import httpx
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.molit_realestate.server import mcp


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


def _xml(body: str) -> httpx.Response:
    return httpx.Response(200, text=body, headers={"content-type": "application/xml"})


async def test_all_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == {"search_property_trades", "search_property_rents"}
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_search_property_trades_returns_normalized_rows(base_url, apt_trade_xml):
    respx.get(url__startswith=base_url).mock(return_value=_xml(apt_trade_xml))
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_property_trades", {"region_code": "11680", "deal_ym": "202608"}
        )

    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["property_type"] == "아파트"
    assert data["total_count"] == 95
    assert data["items"][0]["deal_amount"] == 790000
    assert data["items"][0]["deal_date"] == "2026-08-29"


@respx.mock
async def test_search_property_rents_reports_rent_type(base_url, apt_rent_xml):
    respx.get(url__startswith=base_url).mock(return_value=_xml(apt_rent_xml))
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_property_rents",
            {"region_code": "11680", "deal_ym": "202608", "property_type": "아파트"},
        )

    data = json.loads(_text(result))
    assert [i["rent_type"] for i in data["items"]] == ["월세", "전세"]


@respx.mock
async def test_region_code_from_find_region_code_works_as_is(base_url, apt_trade_xml):
    """nps find_region_code 가 주는 10자리를 그대로 넣어도 동작해야 한다."""
    route = respx.get(url__startswith=base_url).mock(return_value=_xml(apt_trade_xml))
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_property_trades", {"region_code": "1168000000", "deal_ym": "202608"}
        )

    assert route.calls.last.request.url.params["LAWD_CD"] == "11680"
    assert json.loads(_text(result))["region_code"] == "11680"


async def test_bad_region_code_is_input_error():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_property_trades", {"region_code": "11", "deal_ym": "202608"}
        )
    assert result.is_error is True
    assert "입력값 오류" in _text(result) and "지역코드" in _text(result)


async def test_rent_type_without_api_is_input_error():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_property_rents",
            {"region_code": "11680", "deal_ym": "202608", "property_type": "상업업무용"},
        )
    assert result.is_error is True
    assert "전월세" in _text(result)


@respx.mock
async def test_empty_month_is_not_an_error(base_url, empty_xml):
    respx.get(url__startswith=base_url).mock(return_value=_xml(empty_xml))
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_property_trades", {"region_code": "11680", "deal_ym": "202712"}
        )

    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["items"] == [] and data["total_count"] == 0
