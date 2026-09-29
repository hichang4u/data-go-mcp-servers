"""molit 클라이언트 테스트 — 종류별 엔드포인트 분기와 입력 정규화가 핵심."""

import httpx
import pytest
import respx

from data_go_mcp.core import DataGoAPIError
from data_go_mcp.molit_realestate.api_client import MolitRealEstateAPIClient

from .conftest import ERROR_XML


def _xml(body: str) -> httpx.Response:
    return httpx.Response(200, text=body, headers={"content-type": "application/xml"})


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("MOLIT_REALESTATE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API_KEY"):
        MolitRealEstateAPIClient()


@respx.mock
async def test_apartment_trade_normalizes_amount_area_and_date(base_url, apt_trade_xml):
    route = respx.get(f"{base_url}/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev").mock(
        return_value=_xml(apt_trade_xml)
    )
    async with MolitRealEstateAPIClient() as client:
        result = await client.search_trades("11680", "202608", "아파트")

    q = route.calls.last.request.url.params
    assert (q["LAWD_CD"], q["DEAL_YMD"]) == ("11680", "202608")

    first = result["items"][0]
    assert first["name"] == "한양2"
    assert first["deal_amount"] == 790000  # "790,000" 만원 → int
    assert first["deal_date"] == "2026-08-29"
    assert first["exclusive_area"] == 147.41
    assert first["floor"] == 2
    assert first["build_year"] == 1978
    assert first["dong"] == "압구정동" and first["jibun"] == "493"
    assert result["total_count"] == 95


@respx.mock
async def test_cancelled_deal_is_flagged(base_url, apt_trade_xml):
    """해제된 거래(cdealType=O)를 그냥 실거래로 보여주면 시세를 잘못 읽는다."""
    respx.get(url__startswith=base_url).mock(return_value=_xml(apt_trade_xml))
    async with MolitRealEstateAPIClient() as client:
        result = await client.search_trades("11680", "202608", "아파트")

    live, cancelled = result["items"]
    assert live["cancelled"] is False and live["cancel_date"] is None
    assert cancelled["cancelled"] is True and cancelled["cancel_date"] == "2026-09-02"


@respx.mock
async def test_rent_separates_jeonse_from_monthly(base_url, apt_rent_xml):
    respx.get(url__startswith=base_url).mock(return_value=_xml(apt_rent_xml))
    async with MolitRealEstateAPIClient() as client:
        result = await client.search_rents("11680", "202608", "아파트")

    monthly, jeonse = result["items"]
    assert (monthly["deposit"], monthly["monthly_rent"], monthly["rent_type"]) == (
        40000,
        160,
        "월세",
    )
    assert (jeonse["deposit"], jeonse["monthly_rent"], jeonse["rent_type"]) == (150000, 0, "전세")
    assert jeonse["contract_term"] == "26.09~28.09"
    assert jeonse["previous_deposit"] == 120000


@respx.mock
async def test_land_and_house_keep_their_own_area_fields(base_url, land_trade_xml, sh_trade_xml):
    """면적의 뜻이 종류마다 다르다 — 한 필드로 뭉뚱그리지 않는다."""
    respx.get(url__startswith=f"{base_url}/RTMSDataSvcLandTrade").mock(
        return_value=_xml(land_trade_xml)
    )
    respx.get(url__startswith=f"{base_url}/RTMSDataSvcSHTrade").mock(
        return_value=_xml(sh_trade_xml)
    )
    async with MolitRealEstateAPIClient() as client:
        land = (await client.search_trades("11680", "202608", "토지"))["items"][0]
        house = (await client.search_trades("11680", "202608", "단독다가구"))["items"][0]

    assert land["deal_area"] == 3.31 and land["land_use"] == "제2종일반주거지역"
    assert land["exclusive_area"] is None
    assert house["total_floor_area"] == 331.2 and house["plottage_area"] == 179.3
    assert house["house_type"] == "다가구"


@pytest.mark.parametrize(
    "kind, endpoint",
    [
        ("아파트", "RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"),
        ("오피스텔", "RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade"),
        ("연립다세대", "RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade"),
        ("단독다가구", "RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade"),
        ("상업업무용", "RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"),
        ("토지", "RTMSDataSvcLandTrade/getRTMSDataSvcLandTrade"),
    ],
)
@respx.mock
async def test_each_trade_type_hits_its_own_endpoint(base_url, empty_xml, kind, endpoint):
    route = respx.get(f"{base_url}/{endpoint}").mock(return_value=_xml(empty_xml))
    async with MolitRealEstateAPIClient() as client:
        await client.search_trades("11680", "202608", kind)
    assert route.called


@pytest.mark.parametrize(
    "kind, endpoint",
    [
        ("아파트", "RTMSDataSvcAptRent/getRTMSDataSvcAptRent"),
        ("오피스텔", "RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent"),
        ("연립다세대", "RTMSDataSvcRHRent/getRTMSDataSvcRHRent"),
        ("단독다가구", "RTMSDataSvcSHRent/getRTMSDataSvcSHRent"),
    ],
)
@respx.mock
async def test_each_rent_type_hits_its_own_endpoint(base_url, empty_xml, kind, endpoint):
    route = respx.get(f"{base_url}/{endpoint}").mock(return_value=_xml(empty_xml))
    async with MolitRealEstateAPIClient() as client:
        await client.search_rents("11680", "202608", kind)
    assert route.called


async def test_rent_rejects_types_without_a_rent_api():
    """토지·상업업무용에는 전월세 API 가 없다 — 0건이 아니라 오류로 알려준다."""
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(ValueError, match="전월세"):
            await client.search_rents("11680", "202608", "토지")


@respx.mock
async def test_ten_digit_region_code_is_truncated(base_url, empty_xml):
    """find_region_code 는 10자리를 준다. 그대로 보내면 API 가 조용히 0건을 준다."""
    route = respx.get(url__startswith=base_url).mock(return_value=_xml(empty_xml))
    async with MolitRealEstateAPIClient() as client:
        await client.search_trades("1168000000", "202608", "아파트")
    assert route.calls.last.request.url.params["LAWD_CD"] == "11680"


@pytest.mark.parametrize("region", ["1168", "가나다라마", "", "116800000000"])
async def test_bad_region_code_is_rejected(region):
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(ValueError, match="지역코드"):
            await client.search_trades(region, "202608", "아파트")


@pytest.mark.parametrize("ym", ["2026", "20260", "2026-08", "202613"])
async def test_bad_deal_month_is_rejected(ym):
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(ValueError, match="계약년월"):
            await client.search_trades("11680", ym, "아파트")


async def test_unknown_property_type_is_rejected():
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(ValueError, match="종류"):
            await client.search_trades("11680", "202608", "빌라")


@respx.mock
async def test_empty_month_is_an_empty_result(base_url, empty_xml):
    respx.get(url__startswith=base_url).mock(return_value=_xml(empty_xml))
    async with MolitRealEstateAPIClient() as client:
        result = await client.search_trades("11680", "202712", "아파트")
    assert result == {"items": [], "total_count": 0}


@respx.mock
async def test_service_error_raises(base_url):
    respx.get(url__startswith=base_url).mock(return_value=_xml(ERROR_XML))
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.search_trades("11680", "202608", "아파트")
    assert exc.value.result_code == "30"
