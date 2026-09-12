"""fsc MCP 툴 테스트."""

import json
from decimal import Decimal

import httpx
import pytest
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.fsc_financial_info.server import (
    SERVER_NAME,
    decimal_to_str,
    format_financial_amount,
    mcp,
)


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


# --- helpers ---------------------------------------------------------------


@pytest.mark.parametrize(
    "amount, currency, expected",
    [
        (None, "KRW", "N/A"),
        (Decimal("1500000000000"), "KRW", "1.50조원"),
        (Decimal("250000000"), "KRW", "2.50억원"),
        (Decimal("50000"), "KRW", "5만원"),
        (Decimal("999"), "KRW", "999원"),
        (Decimal("250000000"), "USD", "2.50억 USD"),
    ],
)
def test_format_financial_amount(amount, currency, expected):
    assert format_financial_amount(amount, currency) == expected


def test_decimal_to_str_recurses():
    assert decimal_to_str({"a": Decimal("1.5"), "b": [Decimal("2")]}) == {
        "a": "1.5",
        "b": ["2"],
    }


def test_server_name():
    assert SERVER_NAME == "data-go-mcp.fsc-financial-info"


# --- tools -----------------------------------------------------------------


async def test_all_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == {
        "get_summary_financial_statement",
        "get_balance_sheet",
        "get_income_statement",
        "search_company_financial_info",
        "find_corp_number",
        "get_corp_outline",
    }
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_summary_tool_formats_text(base_url, summary_response):
    respx.get(f"{base_url}/getSummFinaStat_V2").mock(
        return_value=httpx.Response(200, json=summary_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_summary_financial_statement",
            {"crno": "1301110006246", "biz_year": "2023"},
        )

    assert result.is_error is False
    text = _text(result)
    assert "요약 재무제표 조회 결과 (총 2건)" in text
    assert "매출액: 258.94조원" in text
    assert "부채비율: 25.36%" in text


@respx.mock
async def test_balance_sheet_tool_shows_change(base_url, balance_response):
    respx.get(f"{base_url}/getBs_V2").mock(
        return_value=httpx.Response(200, json=balance_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_balance_sheet", {"crno": "1301110006246", "biz_year": "2023"}
        )

    text = _text(result)
    assert "[자산총계]" in text
    assert "당기: 455.91조원" in text
    assert "증감: 7.48조원 (+1.7%)" in text


@respx.mock
async def test_empty_result_is_not_an_error(base_url, empty_response):
    respx.get(f"{base_url}/getIncoStat_V2").mock(
        return_value=httpx.Response(200, json=empty_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_income_statement", {"crno": "9999999999999", "biz_year": "2023"}
        )

    assert result.is_error is False
    assert "조회된 손익계산서가 없습니다" in _text(result)


@respx.mock
async def test_comprehensive_search_combines_three_calls(
    base_url, summary_response, balance_response, income_response
):
    respx.get(f"{base_url}/getSummFinaStat_V2").mock(
        return_value=httpx.Response(200, json=summary_response)
    )
    respx.get(f"{base_url}/getBs_V2").mock(
        return_value=httpx.Response(200, json=balance_response)
    )
    respx.get(f"{base_url}/getIncoStat_V2").mock(
        return_value=httpx.Response(200, json=income_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_company_financial_info",
            {"crno": "1301110006246", "biz_year": "2023"},
        )

    text = _text(result)
    assert "📊 요약 재무제표" in text
    assert "📋 재무상태표 주요 항목" in text
    assert "• 자산총계: 455.91조원" in text
    assert "... 외 13개 항목" in text
    assert "💹 손익계산서 주요 항목" in text


@respx.mock
async def test_comprehensive_search_reports_partial_failure(
    base_url, summary_response, income_response
):
    respx.get(f"{base_url}/getSummFinaStat_V2").mock(
        return_value=httpx.Response(200, json=summary_response)
    )
    respx.get(f"{base_url}/getBs_V2").mock(
        return_value=httpx.Response(502, text="bad gateway")
    )
    respx.get(f"{base_url}/getIncoStat_V2").mock(
        return_value=httpx.Response(200, json=income_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_company_financial_info",
            {"crno": "1301110006246", "biz_year": "2023"},
        )

    assert result.is_error is False
    assert "❌ 재무상태표 조회 실패" in _text(result)


async def test_invalid_crno_is_tool_error():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_summary_financial_statement", {"crno": "12", "biz_year": "2023"}
        )

    assert result.is_error is True
    assert "입력값 오류" in _text(result)


@respx.mock
async def test_api_error_is_tool_error(base_url):
    respx.get(f"{base_url}/getSummFinaStat_V2").mock(
        return_value=httpx.Response(
            200,
            json={
                "response": {
                    "header": {"resultCode": "22", "resultMsg": "LIMITED"},
                    "body": {},
                }
            },
        )
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_summary_financial_statement", {"crno": "1301110006246"}
        )

    assert result.is_error is True
    assert "[22] LIMITED" in _text(result)


async def test_missing_api_key_is_tool_error(monkeypatch):
    monkeypatch.delenv("API_KEY")
    async with Client(mcp) as client:
        result = await client.call_tool("get_balance_sheet", {"crno": "1301110006246"})

    assert result.is_error is True
    assert "API_KEY" in _text(result)


# --- 기업기본정보 --------------------------------------------------------------


@respx.mock
async def test_find_corp_number_lists_unique_corporations(corp_base_url, corp_response):
    respx.get(f"{corp_base_url}/getCorpOutline_V2").mock(
        return_value=httpx.Response(200, json=corp_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "find_corp_number", {"corp_name": "삼성전자(주)"}
        )

    assert result.is_error is False
    data = json.loads(_text(result))
    assert [i["crno"] for i in data["items"]] == ["1301110006246", "2845110008637"]
    item = data["items"][0]
    assert item["corp_nm"] == "삼성전자(주)"
    assert item["bzno"] == "1248100998"
    assert item["market"] == "유가"
    assert item["enp_rpr_fnm"] == "전영현, 노태문"
    assert "enp_empe_cnt" not in item  # 목록은 요약 필드만
    assert data["message"] == "Found 2 corporation(s) in 20 record(s) on page 1"


@respx.mock
async def test_find_corp_number_no_match(corp_base_url, empty_response):
    respx.get(f"{corp_base_url}/getCorpOutline_V2").mock(
        return_value=httpx.Response(200, json=empty_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("find_corp_number", {"bzno": "000-00-00000"})

    assert result.is_error is False
    data = json.loads(_text(result))
    assert data["items"] == []
    assert data["message"] == "No corporation found"


async def test_find_corp_number_requires_name_or_bzno():
    async with Client(mcp) as client:
        result = await client.call_tool("find_corp_number", {})

    assert result.is_error is True
    assert "입력값 오류" in _text(result)


@respx.mock
async def test_get_corp_outline_returns_full_latest_snapshot(
    corp_base_url, corp_response
):
    respx.get(f"{corp_base_url}/getCorpOutline_V2").mock(
        return_value=httpx.Response(200, json=corp_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_corp_outline", {"crno": "1301110006246"})

    assert result.is_error is False
    data = json.loads(_text(result))
    assert data["enp_empe_cnt"] == 128881
    assert data["audt_rpt_opnn_ctt"] == "적정의견"
    assert data["snapshot_dt"] == "20260911"


@respx.mock
async def test_get_corp_outline_not_found_is_tool_error(corp_base_url, empty_response):
    respx.get(f"{corp_base_url}/getCorpOutline_V2").mock(
        return_value=httpx.Response(200, json=empty_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_corp_outline", {"crno": "1301110006246"})

    assert result.is_error is True
    assert "1301110006246" in _text(result)
