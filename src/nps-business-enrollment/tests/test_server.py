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
        "find_region_code",
        "get_insurance_status",
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


@respx.mock
async def test_find_region_code_returns_levels_and_nps_params(region_base_url, region_response):
    respx.get(f"{region_base_url}/getStanReginCdList").mock(
        return_value=httpx.Response(200, json=region_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("find_region_code", {"name": "강남구"})

    assert result.is_error is False
    data = json.loads(_text(result))
    assert data["total_count"] == 15
    # 페이지가 전체를 못 담으면 메시지에 드러낸다
    assert (
        data["message"]
        == "Found 15 region(s); showing 3 on page 1 (use page_no or a narrower name)"
    )
    # 상위 단위가 먼저 오도록 정렬 (페이지 안에서): 시군구 → 읍면동 → 리
    assert [i["name"] for i in data["items"]] == [
        "서울특별시 강남구",
        "서울특별시 강남구 역삼동",
        "경기도 가평군 가평읍 읍내리",
    ]
    gu, dong, ri = data["items"]
    assert gu["level"] == "시군구"
    assert gu["nps_params"] == {"ldong_addr_mgpl_dg_cd": "11", "ldong_addr_mgpl_sggu_cd": "680"}
    assert dong["level"] == "읍면동"
    assert dong["nps_params"] == {
        "ldong_addr_mgpl_dg_cd": "11",
        "ldong_addr_mgpl_sggu_cd": "680",
        "ldong_addr_mgpl_sggu_emd_cd": "101",
    }
    # 리는 nps 에 파라미터가 없으므로 소속 읍면동 코드를 준다
    assert ri["level"] == "리"
    assert ri["nps_params"] == {
        "ldong_addr_mgpl_dg_cd": "41",
        "ldong_addr_mgpl_sggu_cd": "820",
        "ldong_addr_mgpl_sggu_emd_cd": "250",
    }


@respx.mock
async def test_find_region_code_no_match_is_not_an_error(region_base_url, region_no_data_response):
    respx.get(f"{region_base_url}/getStanReginCdList").mock(
        return_value=httpx.Response(200, json=region_no_data_response)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("find_region_code", {"name": "없는동네"})

    assert result.is_error is False
    data = json.loads(_text(result))
    assert data["items"] == []
    assert data["message"] == "No regions found matching '없는동네'"


async def test_find_region_code_rejects_blank_name():
    async with Client(mcp) as client:
        result = await client.call_tool("find_region_code", {"name": "  "})

    assert result.is_error is True
    assert "입력값 오류" in _text(result)


@respx.mock
async def test_find_region_code_message_when_page_is_complete(region_base_url, region_response):
    full = json.loads(json.dumps(region_response))
    full["StanReginCd"][0]["head"][0]["totalCount"] = 3
    respx.get(f"{region_base_url}/getStanReginCdList").mock(
        return_value=httpx.Response(200, json=full)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("find_region_code", {"name": "강남구"})

    assert json.loads(_text(result))["message"] == "Found 3 region(s)"


@respx.mock
async def test_get_insurance_status_summarizes_by_kind(insurance_base_url, insurance_xml):
    respx.get(f"{insurance_base_url}/getGySjBoheomBsshItem").mock(
        return_value=httpx.Response(200, text=insurance_xml)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_insurance_status", {"bzno": "120-88-00767"})

    assert result.is_error is False
    data = json.loads(_text(result))
    assert data["total_count"] == 3
    assert [i["insurance"] for i in data["items"]] == ["산재", "고용", "산재"]
    assert data["summary"] == {
        "산재": {"workplaces": 2, "employees": 12081},
        "고용": {"workplaces": 1, "employees": 11070},
    }
    assert (
        data["message"]
        == "1208800767: 3 insured workplace(s) — 산재 2 (12,081명), 고용 1 (11,070명)"
    )


@respx.mock
async def test_get_insurance_status_filters_kind(insurance_base_url, insurance_single_xml):
    route = respx.get(f"{insurance_base_url}/getGySjBoheomBsshItem").mock(
        return_value=httpx.Response(200, text=insurance_single_xml)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_insurance_status", {"bzno": "1248100998", "insurance": "고용"}
        )

    assert route.calls.last.request.url.params["opaBoheomFg"] == "2"
    data = json.loads(_text(result))
    assert data["summary"] == {"고용": {"workplaces": 1, "employees": 128093}}


@respx.mock
async def test_get_insurance_status_none_found(insurance_base_url, insurance_empty_xml):
    respx.get(f"{insurance_base_url}/getGySjBoheomBsshItem").mock(
        return_value=httpx.Response(200, text=insurance_empty_xml)
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_insurance_status", {"bzno": "9999999999"})

    assert result.is_error is False
    data = json.loads(_text(result))
    assert data["items"] == [] and data["summary"] == {}
    assert data["message"] == "9999999999: no insured workplace found"


async def test_get_insurance_status_bad_bzno_is_tool_error():
    async with Client(mcp) as client:
        result = await client.call_tool("get_insurance_status", {"bzno": "12"})

    assert result.is_error is True
    assert "입력값 오류" in _text(result)
