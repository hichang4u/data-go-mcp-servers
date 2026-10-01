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
    assert {t.name for t in tools} == {
        "search_property_trades",
        "search_property_rents",
        "get_building_register",
    }
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


@respx.mock
async def test_get_building_register_tool(apt_trade_xml):
    from .conftest import BLD_BASE, BLD_TITLE_XML

    respx.get(url__startswith=BLD_BASE).mock(return_value=_xml(BLD_TITLE_XML))
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_building_register",
            {"region_code": "1168010500", "bun": "1", "ji": "1"},
        )

    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["kind"] == "표제부"
    assert data["items"][0]["total_floor_area"] == 8862.1
    assert data["items"][0]["approval_date"] == "1978-11-01"


@respx.mock
async def test_trade_exposes_lot_numbers_for_the_building_lookup(base_url, apt_trade_xml):
    """실거래 응답의 본번·부번을 그대로 get_building_register 에 넘길 수 있어야 한다."""
    respx.get(url__startswith=base_url).mock(return_value=_xml(apt_trade_xml))
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_property_trades", {"region_code": "11680", "deal_ym": "202608"}
        )

    first = json.loads(_text(result))["items"][0]
    assert first["bun"] == "0493"
    assert first["ji"] == "0000"


async def test_building_register_bad_kind_is_input_error():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_building_register", {"region_code": "1168010500", "bun": "1", "kind": "등기부"}
        )
    assert result.is_error is True
    assert "대장 종류" in _text(result)
