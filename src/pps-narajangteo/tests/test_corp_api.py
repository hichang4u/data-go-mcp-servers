"""조달업체 정보 (UsrInfoService02) — 사업자번호로 업체·업종·공급물품·제재를 본다.

여기서 꼭 지켜야 하는 것은 ``inqryDiv`` 다. "사업자등록번호 기준검색"의 코드가
오퍼레이션마다 다르다 (기본정보 3, 나머지 1). 하나로 묶으면 조용히 엉뚱한 조회가 된다.
"""

import httpx
import pytest
import respx

from data_go_mcp.core import DataGoAPIError
from data_go_mcp.pps_narajangteo.api_client import PpsNarajangteoAPIClient

from .conftest import (
    CORP_BASE,
    CORP_BASIC,
    CORP_EMPTY,
    CORP_INDUSTRY,
    CORP_SANCTION,
    CORP_SUPPLY,
)


BIZNO = "111-81-26895"


def _mock_profile() -> dict[str, respx.Route]:
    return {
        "basic": respx.get(f"{CORP_BASE}/getPrcrmntCorpBasicInfo02").mock(
            return_value=httpx.Response(200, json=CORP_BASIC)
        ),
        "industry": respx.get(f"{CORP_BASE}/getPrcrmntCorpIndstrytyInfo02").mock(
            return_value=httpx.Response(200, json=CORP_INDUSTRY)
        ),
        "supply": respx.get(f"{CORP_BASE}/getPrcrmntCorpSplyPrdctInfo02").mock(
            return_value=httpx.Response(200, json=CORP_SUPPLY)
        ),
    }


@respx.mock
async def test_profile_gathers_the_three_facets():
    routes = _mock_profile()
    async with PpsNarajangteoAPIClient() as client:
        result = await client.get_procurement_company(BIZNO)

    assert all(r.called for r in routes.values())
    company = result["company"]
    assert company["name"] == "주식회사 레드캡투어"
    assert company["ceo"] == "인유성"
    assert company["business_number"] == "1118126895"
    assert company["employees"] == 499
    assert company["opened_on"] == "1996-08-01"
    assert company["address"] == "서울특별시 중구 을지로 100, 비동 19층(을지로2가, 파인에비뉴)"
    assert company["region"] == "서울특별시 중구"
    assert company["head_office"] == "본사"
    assert company["business_types"] == ["물품", "일반용역", "용역"]

    industries = result["industries"]
    assert len(industries) == 2
    assert industries[0]["name"] == "종합여행업"
    assert any(i["representative"] for i in industries)

    products = result["products"]
    assert products[0]["name"] == "자동차렌트서비스"
    assert products[0]["classification_code"] == "7811180801"
    assert products[0]["manufactured"] is False


@respx.mock
async def test_profile_sends_the_right_inqry_div_per_operation():
    """기본정보만 3, 업종·공급물품은 1. 공유 상수로 묶으면 틀린다."""
    routes = _mock_profile()
    async with PpsNarajangteoAPIClient() as client:
        await client.get_procurement_company(BIZNO)

    assert routes["basic"].calls.last.request.url.params["inqryDiv"] == "3"
    assert routes["industry"].calls.last.request.url.params["inqryDiv"] == "1"
    assert routes["supply"].calls.last.request.url.params["inqryDiv"] == "1"
    for route in routes.values():
        assert route.calls.last.request.url.params["bizno"] == "1118126895"


@respx.mock
async def test_unregistered_company_is_not_an_error():
    """조달 등록이 없는 사업자번호는 0건이지 오류가 아니다."""
    respx.get(url__startswith=CORP_BASE).mock(return_value=httpx.Response(200, json=CORP_EMPTY))
    async with PpsNarajangteoAPIClient() as client:
        result = await client.get_procurement_company("999-99-99999")

    assert result["company"] is None
    assert result["registered"] is False
    assert result["industries"] == [] and result["products"] == []


@respx.mock
async def test_sanctions_report_the_restriction():
    route = respx.get(f"{CORP_BASE}/getUnptRsttCorpInfo02").mock(
        return_value=httpx.Response(200, json=CORP_SANCTION)
    )
    async with PpsNarajangteoAPIClient() as client:
        result = await client.check_procurement_sanctions("327-81-00184")

    assert route.calls.last.request.url.params["inqryDiv"] == "1"
    assert result["total_count"] == 1
    first = result["items"][0]
    assert first["company_name"] == "주식회사 세연인터내셔널"
    assert first["institution"] == "방위사업청"
    assert first["begins_on"] == "2026-02-26"
    assert first["ends_on"] == "2026-11-25"
    assert first["months"] == 9
    assert first["status"] == "제재"
    assert "계약을 체결 또는 이행" in first["reason"]


@respx.mock
async def test_sanctions_say_whether_one_is_in_effect_today(monkeypatch):
    """제재 이력이 있는 것과 지금 제재 중인 것은 다른 질문이다."""
    respx.get(url__startswith=CORP_BASE).mock(return_value=httpx.Response(200, json=CORP_SANCTION))

    import datetime as dt

    class _Clock(dt.date):
        @classmethod
        def today(cls) -> "dt.date":
            return dt.date(2026, 6, 1)  # 2026-02-26 ~ 11-25 사이

    monkeypatch.setattr("data_go_mcp.pps_narajangteo.api_client.dt.date", _Clock)
    async with PpsNarajangteoAPIClient() as client:
        result = await client.check_procurement_sanctions("327-81-00184")
    assert result["restricted_now"] is True
    assert result["items"][0]["in_effect"] is True


@respx.mock
async def test_clean_company_has_no_sanctions():
    respx.get(url__startswith=CORP_BASE).mock(return_value=httpx.Response(200, json=CORP_EMPTY))
    async with PpsNarajangteoAPIClient() as client:
        result = await client.check_procurement_sanctions(BIZNO)
    assert result == {
        "items": [],
        "total_count": 0,
        "complete": True,
        "restricted_now": False,
    }


@pytest.mark.parametrize("value", ["", "111-81-2689", "abc", "11181268950"])
async def test_business_number_must_be_ten_digits(value):
    """틀린 값을 보내면 data.go.kr 은 조용히 0건을 준다 — 보내기 전에 막는다."""
    async with PpsNarajangteoAPIClient() as client:
        with pytest.raises(ValueError, match="사업자번호"):
            await client.get_procurement_company(value)
        with pytest.raises(ValueError, match="사업자번호"):
            await client.check_procurement_sanctions(value)


@respx.mock
async def test_api_error_is_raised_not_swallowed():
    respx.get(url__startswith=CORP_BASE).mock(
        return_value=httpx.Response(
            200,
            json={
                "response": {
                    "header": {"resultCode": "30", "resultMsg": "SERVICE_KEY_IS_NOT_REGISTERED"},
                    "body": {},
                }
            },
        )
    )
    async with PpsNarajangteoAPIClient() as client:
        with pytest.raises(DataGoAPIError):
            await client.get_procurement_company(BIZNO)


@respx.mock
async def test_profile_reports_the_api_totals():
    """100건만 받아 오므로, 더 있는지를 알 수 있어야 한다 (삼성전자 공급물품이 이미 68건)."""
    _mock_profile()
    async with PpsNarajangteoAPIClient() as client:
        result = await client.get_procurement_company(BIZNO)

    assert result["industry_count"] == 3  # fixture 는 2행이지만 totalCount 는 3
    assert len(result["industries"]) == 2
    assert result["product_count"] == 2
    assert result["complete"] is False  # 업종을 다 받지 못했다


@respx.mock
async def test_profile_is_complete_when_everything_fits():
    respx.get(f"{CORP_BASE}/getPrcrmntCorpBasicInfo02").mock(
        return_value=httpx.Response(200, json=CORP_BASIC)
    )
    respx.get(f"{CORP_BASE}/getPrcrmntCorpIndstrytyInfo02").mock(
        return_value=httpx.Response(200, json=CORP_SUPPLY)  # 2행 / totalCount 2
    )
    respx.get(f"{CORP_BASE}/getPrcrmntCorpSplyPrdctInfo02").mock(
        return_value=httpx.Response(200, json=CORP_SUPPLY)
    )
    async with PpsNarajangteoAPIClient() as client:
        result = await client.get_procurement_company(BIZNO)
    assert result["complete"] is True


@respx.mock
async def test_sanctions_use_the_api_total_not_the_row_count():
    """페이지 2에 살아 있는 제재가 있어도 restricted_now 가 놓치면 안 된다."""
    respx.get(url__startswith=CORP_BASE).mock(return_value=httpx.Response(200, json=CORP_SANCTION))
    async with PpsNarajangteoAPIClient() as client:
        result = await client.check_procurement_sanctions("327-81-00184")
    assert result["total_count"] == 1  # CORP_SANCTION 의 totalCount
    assert result["complete"] is True


@respx.mock
async def test_a_failing_facet_does_not_leave_tasks_behind(monkeypatch):
    """한 오퍼레이션이 실패해도 나머지를 버려두고 커넥션을 닫으면 안 된다."""
    respx.get(f"{CORP_BASE}/getPrcrmntCorpBasicInfo02").mock(
        return_value=httpx.Response(
            200, json={"response": {"header": {"resultCode": "30", "resultMsg": "NO KEY"}}}
        )
    )
    respx.get(f"{CORP_BASE}/getPrcrmntCorpIndstrytyInfo02").mock(
        return_value=httpx.Response(200, json=CORP_INDUSTRY)
    )
    respx.get(f"{CORP_BASE}/getPrcrmntCorpSplyPrdctInfo02").mock(
        return_value=httpx.Response(200, json=CORP_SUPPLY)
    )
    seen: list[str] = []
    import asyncio

    loop = asyncio.get_running_loop()
    loop.set_exception_handler(lambda _loop, ctx: seen.append(str(ctx.get("message", ""))))

    async with PpsNarajangteoAPIClient() as client:
        with pytest.raises(DataGoAPIError):
            await client.get_procurement_company(BIZNO)
    await asyncio.sleep(0)
    assert not [m for m in seen if "never retrieved" in m]
