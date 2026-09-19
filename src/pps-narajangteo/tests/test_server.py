"""pps MCP 툴 테스트."""

import json
import re
from datetime import datetime

import httpx
import pytest
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.pps_narajangteo.server import format_datetime_for_api, mcp, parse_business_type


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


# --- helpers ---------------------------------------------------------------


@pytest.mark.parametrize(
    "value, is_end, expected",
    [
        ("2026-09-01", False, "202609010000"),
        ("2026-09-01", True, "202609012359"),
        ("20260901", False, "202609010000"),
        ("202609011230", True, "202609011230"),
    ],
)
def test_format_datetime_for_api(value, is_end, expected):
    assert format_datetime_for_api(value, is_end=is_end) == expected


def test_format_datetime_rejects_garbage():
    with pytest.raises(ValueError, match="잘못된 날짜"):
        format_datetime_for_api("2026/9")


@pytest.mark.parametrize(
    "name, code", [("물품", "1"), ("외자", "2"), ("공사", "3"), ("용역", "5"), ("3", "3")]
)
def test_parse_business_type(name, code):
    assert parse_business_type(name) == code


# --- tools -----------------------------------------------------------------


async def test_all_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == {
        "search_bid_announcements",
        "search_successful_bids",
        "search_contracts",
        "get_bid_detail",
    }
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_search_bid_announcements_with_explicit_range(base_url, ok_response, bid_item):
    route = respx.get(f"{base_url}/getDataSetOpnStdBidPblancInfo").mock(
        return_value=httpx.Response(200, json=ok_response([bid_item], total=57))
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_bid_announcements", {"start_date": "2026-09-01", "end_date": "2026-09-12"}
        )

    q = route.calls.last.request.url.params
    assert q["bidNtceBgnDt"] == "202609010000"
    assert q["bidNtceEndDt"] == "202609122359"

    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["success"] is True
    assert data["total_count"] == 57
    assert data["items"][0]["bidNtceNo"] == "R26BK01722116"
    assert data["search_period"] == "20260901 ~ 20260912"


@respx.mock
async def test_search_bid_announcements_defaults_to_today(base_url, ok_response):
    route = respx.get(f"{base_url}/getDataSetOpnStdBidPblancInfo").mock(
        return_value=httpx.Response(200, json=ok_response([]))
    )
    async with Client(mcp) as client:
        await client.call_tool("search_bid_announcements", {})

    q = route.calls.last.request.url.params
    assert re.fullmatch(r"\d{8}0000", q["bidNtceBgnDt"])
    assert re.fullmatch(r"\d{8}2359", q["bidNtceEndDt"])
    assert q["bidNtceBgnDt"][:8] == q["bidNtceEndDt"][:8]


@respx.mock
async def test_search_successful_bids_maps_business_type(base_url, ok_response):
    route = respx.get(f"{base_url}/getDataSetOpnStdScsbidInfo").mock(
        return_value=httpx.Response(200, json=ok_response([]))
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_successful_bids",
            {"business_type": "공사", "start_date": "2026-09-11"},
        )

    q = route.calls.last.request.url.params
    assert q["bsnsDivCd"] == "3"
    assert (q["opengBgnDt"], q["opengEndDt"]) == ("202609110000", "202609112359")
    data = json.loads(_text(result))
    assert data["business_type"] == "공사"
    assert data["search_period"] == "20260911 ~ 20260911"


@respx.mock
async def test_search_contracts_passes_institution_filter(base_url, ok_response):
    route = respx.get(f"{base_url}/getDataSetOpnStdCntrctInfo").mock(
        return_value=httpx.Response(200, json=ok_response([]))
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_contracts",
            {"start_date": "2026-09-01", "institution_type": "2", "institution_code": "1234567"},
        )

    q = route.calls.last.request.url.params
    assert q["cntrctCnclsBgnDate"] == "20260901"
    assert q["cntrctCnclsEndDate"] == "20260901"
    assert q["insttDivCd"] == "2"
    assert q["insttCd"] == "1234567"
    assert json.loads(_text(result))["institution_filter"] == {"type": "2", "code": "1234567"}


@respx.mock
async def test_get_bid_detail_finds_notice_in_window(base_url, ok_response, bid_item):
    other = {**bid_item, "bidNtceNo": "R26BK00000001"}
    route = respx.get(f"{base_url}/getDataSetOpnStdBidPblancInfo").mock(
        return_value=httpx.Response(200, json=ok_response([other, bid_item], total=2))
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_bid_detail",
            {
                "bid_notice_no": "R26BK01722116",
                "start_date": "2026-09-01",
                "end_date": "2026-09-12",
            },
        )

    assert route.calls.last.request.url.params["numOfRows"] == "999"
    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["data"]["bidNtceNm"] == "2026년 도로 유지보수 공사"


@respx.mock
async def test_get_bid_detail_not_found_is_tool_error(base_url, ok_response):
    respx.get(f"{base_url}/getDataSetOpnStdBidPblancInfo").mock(
        return_value=httpx.Response(200, json=ok_response([]))
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_bid_detail", {"bid_notice_no": "R00"})

    assert result.is_error is True
    assert "R00" in _text(result)


async def test_bad_date_is_input_error():
    async with Client(mcp) as client:
        result = await client.call_tool("search_bid_announcements", {"start_date": "2026/9"})

    assert result.is_error is True
    assert "입력값 오류" in _text(result)


@respx.mock
async def test_api_error_is_tool_error(base_url):
    respx.get(f"{base_url}/getDataSetOpnStdBidPblancInfo").mock(
        return_value=httpx.Response(
            200,
            json={
                "response": {"header": {"resultCode": "22", "resultMsg": "LIMITED"}, "body": {}}
            },
        )
    )
    async with Client(mcp) as client:
        result = await client.call_tool("search_bid_announcements", {"start_date": "2026-09-01"})

    assert result.is_error is True
    assert "[22] LIMITED" in _text(result)


@pytest.mark.parametrize(
    "today, expected",
    [
        (datetime(2026, 9, 20, 10), "20260918"),  # 일요일 → 금요일
        (datetime(2026, 9, 21, 9), "20260918"),  # 월요일 → 금요일
        (datetime(2026, 9, 22, 18), "20260921"),  # 화요일 → 월요일
    ],
)
@respx.mock
async def test_search_successful_bids_defaults_to_previous_weekday(
    base_url, ok_response, monkeypatch, today, expected
):
    """낙찰 API 는 하루 범위만 받는다 (2026-09-20 실호출: 2일부터 코드 07). 기본은 직전 평일 —
    당일 개찰은 진행 중이라 불완전하다."""
    import data_go_mcp.pps_narajangteo.server as srv

    class Fixed(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(today.year, today.month, today.day, today.hour)

    monkeypatch.setattr(srv, "datetime", Fixed)
    route = respx.get(f"{base_url}/getDataSetOpnStdScsbidInfo").mock(
        return_value=httpx.Response(200, json=ok_response([]))
    )
    async with Client(mcp) as client:
        result = await client.call_tool("search_successful_bids", {})

    q = route.calls.last.request.url.params
    assert (q["opengBgnDt"], q["opengEndDt"]) == (f"{expected}0000", f"{expected}2359")
    assert json.loads(_text(result))["search_period"] == f"{expected} ~ {expected}"


@respx.mock
async def test_search_contracts_limit_is_seven_days(base_url, ok_response):
    """계약 API 의 실제 한도는 7일 (2026-09-20 실호출: 8일부터 코드 07). 문서의 1개월이 아니다."""
    route = respx.get(f"{base_url}/getDataSetOpnStdCntrctInfo").mock(
        return_value=httpx.Response(200, json=ok_response([]))
    )
    async with Client(mcp) as client:
        ok = await client.call_tool(
            "search_contracts", {"start_date": "2026-09-12", "end_date": "2026-09-18"}
        )
        bad = await client.call_tool(
            "search_contracts", {"start_date": "2026-09-11", "end_date": "2026-09-18"}
        )
    assert ok.is_error is False
    assert bad.is_error is True and "7일" in _text(bad)
    assert route.call_count == 1


@respx.mock
async def test_get_bid_detail_scans_default_week_up_to_page_limit(
    base_url, ok_response, monkeypatch, bid_item
):
    """단건 API 가 없어 훑는다. 하루 1,100건 이상이라 기본 범위는 7일, 999건 × 최대 12페이지."""
    import data_go_mcp.pps_narajangteo.server as srv

    class Fixed(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 18, 12)

    monkeypatch.setattr(srv, "datetime", Fixed)
    filler = [{**bid_item, "bidNtceNo": f"R26BK{i:08d}"} for i in range(999)]
    route = respx.get(f"{base_url}/getDataSetOpnStdBidPblancInfo").mock(
        return_value=httpx.Response(200, json=ok_response(filler, total=99999))
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_bid_detail", {"bid_notice_no": "R26BK99999999"})

    assert result.is_error is True
    assert route.call_count == 12
    q = route.calls[0].request.url.params
    assert (q["bidNtceBgnDt"], q["bidNtceEndDt"]) == ("202609110000", "202609182359")


async def test_search_successful_bids_rejects_multi_day_range():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_successful_bids", {"start_date": "2026-09-17", "end_date": "2026-09-18"}
        )
    assert result.is_error is True
    assert "하루" in _text(result)
