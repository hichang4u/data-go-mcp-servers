"""낙찰업체 조회 클라이언트 테스트.

API 가 업체로 필터해 주지 않아 기간을 훑어 거른다 (2026-09-30 확인). 전수는 ``PPSSrch`` 가
붙지 않은 오퍼레이션이고, 개찰일시 기준은 ``inqryDiv=2`` 다.
"""

import httpx
import pytest
import respx

from data_go_mcp.pps_narajangteo.api_client import PpsNarajangteoAPIClient

from .conftest import SCSBID_BASE


def _rows(count: int, bizno: str = "6068127392", start: int = 0) -> list[dict]:
    return [
        {
            "bidNtceNo": f"R26BK{i:08d}",
            "bidNtceNm": f"용역 {i}",
            "bidwinnrNm": "하나렌트카주식회사",
            "bidwinnrBizno": bizno,
            "bidwinnrCeoNm": "김용진",
            "sucsfbidAmt": "12340000",
            "sucsfbidRate": "88.5",
            "rlOpengDt": "2026-08-26 11:00:00",
            "dminsttNm": "한국주택금융공사",
        }
        for i in range(start, start + count)
    ]


def _page(items: list[dict], total: int) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "response": {
                "header": {"resultCode": "00", "resultMsg": "정상"},
                "body": {"items": items, "numOfRows": 999, "pageNo": 1, "totalCount": total},
            }
        },
    )


@respx.mock
async def test_scans_by_opening_date_on_the_full_dataset():
    """전수(PPSSrch 없음) + 개찰일시(inqryDiv=2) 로 조회해야 한다."""
    route = respx.get(f"{SCSBID_BASE}/getScsbidListSttusServc").mock(
        return_value=_page(_rows(2), total=2)
    )
    async with PpsNarajangteoAPIClient() as client:
        await client.find_bid_winners(
            business_number="6068127392", start_date="2026-08-01", end_date="2026-08-31"
        )

    q = route.calls.last.request.url.params
    assert q["inqryDiv"] == "2"
    assert (q["inqryBgnDt"], q["inqryEndDt"]) == ("202608010000", "202608312359")
    assert q["numOfRows"] == "999"


@respx.mock
async def test_business_number_matches_with_or_without_hyphens():
    respx.get(url__startswith=SCSBID_BASE).mock(
        return_value=_page(_rows(1, bizno="2148712538") + _rows(1, bizno="9999999999"), total=2)
    )
    async with PpsNarajangteoAPIClient() as client:
        result = await client.find_bid_winners(
            business_number="214-87-12538", start_date="2026-08-01", end_date="2026-08-31"
        )

    assert result["total_count"] == 1
    assert result["items"][0]["business_number"] == "2148712538"
    assert result["scanned_count"] == 2


@respx.mock
async def test_company_name_is_a_partial_match():
    respx.get(url__startswith=SCSBID_BASE).mock(
        return_value=_page(_rows(1) + _rows(1, bizno="9999999999", start=5), total=2)
    )
    async with PpsNarajangteoAPIClient() as client:
        result = await client.find_bid_winners(
            company_name="하나렌트", start_date="2026-08-01", end_date="2026-08-31"
        )
    assert len(result["items"]) == 2  # 두 행 모두 같은 업체명


@respx.mock
async def test_pages_until_the_window_is_exhausted():
    route = respx.get(url__startswith=SCSBID_BASE).mock(
        side_effect=[
            _page(_rows(999), total=1500),
            _page(_rows(501, start=999), total=1500),
        ]
    )
    async with PpsNarajangteoAPIClient() as client:
        result = await client.find_bid_winners(
            business_number="6068127392", start_date="2026-08-01", end_date="2026-08-31"
        )
    assert route.call_count == 2
    assert result["scanned_count"] == 1500


@pytest.mark.parametrize(
    "kind, endpoint",
    [
        ("용역", "getScsbidListSttusServc"),
        ("물품", "getScsbidListSttusThng"),
        ("공사", "getScsbidListSttusCnstwk"),
        ("외자", "getScsbidListSttusFrgcpt"),
    ],
)
@respx.mock
async def test_each_business_type_hits_its_own_endpoint(kind, endpoint):
    route = respx.get(f"{SCSBID_BASE}/{endpoint}").mock(return_value=_page([], total=0))
    async with PpsNarajangteoAPIClient() as client:
        await client.find_bid_winners(
            business_number="6068127392",
            business_type=kind,
            start_date="2026-08-01",
            end_date="2026-08-31",
        )
    assert route.called


async def test_requires_a_business_number_or_name():
    async with PpsNarajangteoAPIClient() as client:
        with pytest.raises(ValueError, match="사업자번호|업체명"):
            await client.find_bid_winners(start_date="2026-08-01", end_date="2026-08-31")


async def test_range_longer_than_three_months_is_rejected():
    """전수를 훑는 방식이라 기간이 길면 분 단위로 늘어난다 (3개월 약 70초)."""
    async with PpsNarajangteoAPIClient() as client:
        with pytest.raises(ValueError, match="3개월"):
            await client.find_bid_winners(
                business_number="6068127392", start_date="2026-01-01", end_date="2026-08-31"
            )


@respx.mock
async def test_defaults_to_the_last_month(monkeypatch):
    import data_go_mcp.pps_narajangteo.api_client as mod

    class Fixed(mod.dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 30, 12)

    monkeypatch.setattr(mod.dt, "datetime", Fixed)
    route = respx.get(url__startswith=SCSBID_BASE).mock(return_value=_page([], total=0))
    async with PpsNarajangteoAPIClient() as client:
        await client.find_bid_winners(business_number="6068127392")

    q = route.calls.last.request.url.params
    assert (q["inqryBgnDt"], q["inqryEndDt"]) == ("202608310000", "202609302359")


@respx.mock
async def test_amounts_and_dates_are_normalized():
    respx.get(url__startswith=SCSBID_BASE).mock(return_value=_page(_rows(1), total=1))
    async with PpsNarajangteoAPIClient() as client:
        result = await client.find_bid_winners(
            business_number="6068127392", start_date="2026-08-01", end_date="2026-08-31"
        )
    item = result["items"][0]
    assert item["winning_amount"] == 12340000
    assert item["winning_rate"] == 88.5
    assert item["opening_date"] == "2026-08-26"
    assert item["company_name"] == "하나렌트카주식회사"
    assert item["demand_institution"] == "한국주택금융공사"
