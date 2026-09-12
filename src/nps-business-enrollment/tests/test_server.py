"""NPS MCP 툴 테스트 — 인프로세스 mcp.Client 로 호출하고 HTTP만 respx로 가로챈다."""

import json

import httpx
import pytest
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.nps_business_enrollment.server import mcp


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


async def test_all_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == {
        "search_business",
        "get_business_detail",
        "get_period_status",
    }
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_search_business_returns_items_and_message(base_url, search_response):
    respx.get(f"{base_url}/getBassInfoSearchV2").mock(
        return_value=httpx.Response(200, json=search_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("search_business", {"wkpl_nm": "삼성전자"})

    assert result.is_error is False
    data = json.loads(_text(result))
    assert data["total_count"] == 2107
    assert data["items"][0]["wkpl_nm"] == "주식회사 유일이엔지"
    assert data["message"] == "Found 2107 business(es)"


@respx.mock
async def test_get_business_detail_adds_estimated_salary(base_url, detail_response):
    respx.get(f"{base_url}/getDetailInfoSearchV2").mock(
        return_value=httpx.Response(200, json=detail_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_business_detail", {"seq": 7101020})

    item = json.loads(_text(result))["items"][0]
    # 7979660 / 36 / 0.09 = 2462858.0…
    assert item["estimated_avg_monthly_salary"] == 2462858
    assert item["estimated_avg_monthly_salary_note"] == "추정값 (당월고지금액 기준)"


@respx.mock
async def test_get_period_status_includes_salary_from_detail(
    base_url, detail_response, period_response
):
    respx.get(f"{base_url}/getPdAcctoSttusInfoSearchV2").mock(
        return_value=httpx.Response(200, json=period_response)
    )
    respx.get(f"{base_url}/getDetailInfoSearchV2").mock(
        return_value=httpx.Response(200, json=detail_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_period_status", {"seq": 7101020, "data_crt_ym": "202607"}
        )

    data = json.loads(_text(result))
    assert data["items"] == [{"nw_acqzr_cnt": 36, "lss_jnngp_cnt": 7}]
    assert data["estimated_avg_monthly_salary"] == 2462858
    assert data["message"].endswith("for 202607")


@respx.mock
async def test_api_error_is_reported_as_tool_error(base_url):
    respx.get(f"{base_url}/getBassInfoSearchV2").mock(
        return_value=httpx.Response(
            200,
            json={"response": {"header": {"resultCode": "30", "resultMsg": "KEY"}, "body": {}}},
        )
    )
    async with Client(mcp) as client:
        result = await client.call_tool("search_business", {"wkpl_nm": "x"})

    assert result.is_error is True
    assert "data.go.kr 오류 [30] KEY" in _text(result)


@respx.mock
async def test_network_error_is_reported_as_tool_error(base_url):
    respx.get(f"{base_url}/getBassInfoSearchV2").mock(side_effect=httpx.ConnectError("refused"))
    async with Client(mcp) as client:
        result = await client.call_tool("search_business", {"wkpl_nm": "x"})

    assert result.is_error is True
    assert "네트워크 오류" in _text(result)


async def test_missing_api_key_is_reported_as_tool_error(monkeypatch):
    monkeypatch.delenv("API_KEY")
    async with Client(mcp) as client:
        result = await client.call_tool("search_business", {"wkpl_nm": "x"})

    assert result.is_error is True
    assert "API_KEY" in _text(result)
