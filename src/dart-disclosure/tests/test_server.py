"""MCP 툴 테스트 — 인프로세스 mcp.Client + respx."""

import json

import httpx
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.dart_disclosure.server import mcp


EXPECTED_TOOLS = {
    "find_corp_code",
    "get_company",
    "list_disclosures",
    "get_key_accounts",
    "get_financial_statements",
    "get_disclosure_document",
}


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


def _data(result) -> dict:
    assert result.is_error is False, _text(result)
    return json.loads(_text(result))


async def test_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == EXPECTED_TOOLS
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        assert tool.description and "|" in tool.description  # 한/영 병기
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


# -- find_corp_code (스냅샷, HTTP 없음) ------------------------------------------


@respx.mock
async def test_find_corp_code_uses_bundled_snapshot_without_http():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "find_corp_code", {"query": "삼성전자", "listed_only": True}
        )
    data = _data(result)
    assert not respx.calls
    assert data["items"][0]["corp_code"] == "00126380"
    assert data["items"][0]["stock_code"] == "005930"
    assert data["total_count"] >= 1
    assert data["snapshot_date"].isdigit()


async def test_find_corp_code_blank_query_is_error():
    async with Client(mcp) as client:
        result = await client.call_tool("find_corp_code", {"query": " "})
    assert result.is_error is True
    assert "입력값 오류" in _text(result)


# -- get_company -------------------------------------------------------------


@respx.mock
async def test_get_company_returns_profile(base_url, company_response):
    respx.get(f"{base_url}/company.json").mock(
        return_value=httpx.Response(200, json=company_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_company", {"corp_code": "00126380"})
    data = _data(result)
    assert data["corp_name"] == "삼성전자(주)"
    assert data["corp_cls_name"] == "유가증권시장"
    assert data["jurir_no"] == "1301110006246"


@respx.mock
async def test_get_company_unknown_code_is_error(base_url, no_data_response):
    respx.get(f"{base_url}/company.json").mock(
        return_value=httpx.Response(200, json=no_data_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_company", {"corp_code": "99999999"})
    assert result.is_error is True
    assert "99999999" in _text(result)


# -- list_disclosures --------------------------------------------------------


@respx.mock
async def test_list_disclosures_returns_items(base_url, disclosure_list_response):
    route = respx.get(f"{base_url}/list.json").mock(
        return_value=httpx.Response(200, json=disclosure_list_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "list_disclosures",
            {"corp_code": "00126380", "bgn_de": "20250101", "end_de": "20250331", "page_count": 5},
        )
    data = _data(result)
    assert route.calls.last.request.url.params["crtfc_key"] == "dart-test-key"
    assert data["total_count"] == 49
    assert data["items"][0]["report_nm"] == "대표이사(대표집행임원)변경(안내공시)"


@respx.mock
async def test_list_disclosures_api_error_is_tool_error(base_url, period_too_long_response):
    respx.get(f"{base_url}/list.json").mock(
        return_value=httpx.Response(200, json=period_too_long_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "list_disclosures", {"bgn_de": "20240101", "end_de": "20250101"}
        )
    assert result.is_error is True
    assert "OpenDART 오류 [100]" in _text(result)


# -- 재무제표 ----------------------------------------------------------------


@respx.mock
async def test_get_key_accounts_returns_int_amounts(base_url, key_accounts_response):
    respx.get(f"{base_url}/fnlttSinglAcnt.json").mock(
        return_value=httpx.Response(200, json=key_accounts_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_key_accounts", {"corp_code": "00126380", "bsns_year": "2024"}
        )
    data = _data(result)
    assert data["items"][0]["thstrm_amount"] == 514_531_948_000_000
    assert data["reprt_code"] == "11011"


@respx.mock
async def test_get_financial_statements_filters_sj_div(base_url, fs_all_response):
    route = respx.get(f"{base_url}/fnlttSinglAcntAll.json").mock(
        return_value=httpx.Response(200, json=fs_all_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_financial_statements",
            {"corp_code": "00126380", "bsns_year": "2024", "fs_div": "OFS", "sj_div": "IS"},
        )
    data = _data(result)
    assert route.calls.last.request.url.params["fs_div"] == "OFS"
    assert data["items"] and all(i["sj_div"] == "IS" for i in data["items"])


# -- 공시 원문 ----------------------------------------------------------------


@respx.mock
async def test_get_disclosure_document_pages_text(base_url, document_zip):
    respx.get(f"{base_url}/document.xml").mock(
        return_value=httpx.Response(200, content=document_zip)
    )
    async with Client(mcp) as client:
        full = _data(
            await client.call_tool("get_disclosure_document", {"rcept_no": "20250325800172"})
        )
        page = _data(
            await client.call_tool(
                "get_disclosure_document",
                {"rcept_no": "20250325800172", "offset": 3, "max_chars": 5},
            )
        )
    assert full["truncated"] is False
    assert full["text"].startswith("대표이사 변경")
    assert full["total_chars"] == len(full["text"])
    assert full["attachment_files"] == ["20250325800172_00001.xml"]

    assert page["text"] == full["text"][3:8]
    assert page["truncated"] is True
    assert page["next_offset"] == 8
    assert page["total_chars"] == full["total_chars"]


@respx.mock
async def test_get_disclosure_document_bad_rcept_no_is_error(base_url, document_error_xml):
    respx.get(f"{base_url}/document.xml").mock(
        return_value=httpx.Response(
            200, text=document_error_xml, headers={"content-type": "application/xml;charset=UTF-8"}
        )
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_disclosure_document", {"rcept_no": "00000000000000"})
    assert result.is_error is True
    assert "접수번호 오류" in _text(result)


# -- 키 ---------------------------------------------------------------------


async def test_missing_dart_key_is_error_even_with_common_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "data-go-key")
    monkeypatch.delenv("DART_DISCLOSURE_API_KEY")
    async with Client(mcp) as client:
        result = await client.call_tool("get_company", {"corp_code": "00126380"})
    assert result.is_error is True
    assert "DART_DISCLOSURE_API_KEY" in _text(result)
    assert "or API_KEY" not in _text(result)


@respx.mock
async def test_get_disclosure_document_pages_download_once(base_url, document_zip):
    route = respx.get(f"{base_url}/document.xml").mock(
        return_value=httpx.Response(200, content=document_zip)
    )
    async with Client(mcp) as client:
        for offset in (0, 5, 10):
            _data(
                await client.call_tool(
                    "get_disclosure_document",
                    {"rcept_no": "20250325800172", "offset": offset, "max_chars": 5},
                )
            )
    assert route.call_count == 1
