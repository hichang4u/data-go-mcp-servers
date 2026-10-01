"""건축물대장 클라이언트 테스트 — 지번 분해와 503 재시도가 핵심."""

import httpx
import pytest
import respx

from data_go_mcp.core import DataGoAPIError
from data_go_mcp.molit_realestate.api_client import MolitRealEstateAPIClient

from .conftest import BLD_BASE, BLD_EMPTY_XML, BLD_FLOOR_XML, BLD_TIMEOUT_XML, BLD_TITLE_XML


def _xml(body: str, status: int = 200) -> httpx.Response:
    return httpx.Response(status, text=body, headers={"content-type": "application/xml"})


@respx.mock
async def test_title_register_normalizes_the_building():
    route = respx.get(f"{BLD_BASE}/getBrTitleInfo").mock(return_value=_xml(BLD_TITLE_XML))
    async with MolitRealEstateAPIClient() as client:
        result = await client.get_building_register("11680", "10500", bun="1", ji="1")

    q = route.calls.last.request.url.params
    assert q["sigunguCd"] == "11680" and q["bjdongCd"] == "10500"
    assert (q["bun"], q["ji"]) == ("0001", "0001")  # 네 자리로 채워 보낸다

    first = result["items"][0]
    assert first["building_name"] is None  # 공백 한 칸으로 오는 것은 None
    assert first["address"] == "서울특별시 강남구 삼성동 1-1번지"
    assert first["road_address"] == "서울특별시 강남구 학동로 402 (삼성동)"
    assert first["main_purpose"] == "업무시설"
    assert first["total_floor_area"] == 8862.1
    assert first["land_area"] == 2003.6
    assert first["floor_area_ratio"] == 367.75
    assert first["structure"] == "철근콘크리트구조"
    assert first["approval_date"] == "1978-11-01"
    assert first["register_kind"] == "일반건축물"
    assert result["total_count"] == 1


@respx.mock
async def test_floor_outline_uses_its_own_endpoint():
    route = respx.get(f"{BLD_BASE}/getBrFlrOulnInfo").mock(return_value=_xml(BLD_FLOOR_XML))
    async with MolitRealEstateAPIClient() as client:
        result = await client.get_building_register(
            "11680", "10500", bun="1", ji="1", kind="층별개요"
        )
    assert route.called
    assert result["items"][0]["floor_name"] == "지하1층"
    assert result["items"][0]["floor_type"] == "지하"
    assert result["items"][0]["area"] == 1459.44


async def test_unknown_register_kind_is_rejected():
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(ValueError, match="대장 종류"):
            await client.get_building_register("11680", "10500", bun="1", kind="등기부")


@pytest.mark.parametrize("bun", ["", "abc", "12345"])
async def test_bad_lot_number_is_rejected(bun):
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(ValueError, match="본번"):
            await client.get_building_register("11680", "10500", bun=bun)


async def test_bjdong_code_must_be_five_digits():
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(ValueError, match="법정동"):
            await client.get_building_register("11680", "105", bun="1")


@respx.mock
async def test_region_code_accepts_the_ten_digit_form():
    """find_region_code 가 주는 1168010500 을 시군구+법정동으로 쪼갠다."""
    route = respx.get(url__startswith=BLD_BASE).mock(return_value=_xml(BLD_TITLE_XML))
    async with MolitRealEstateAPIClient() as client:
        await client.get_building_register("1168010500", bun="1", ji="1")
    q = route.calls.last.request.url.params
    assert (q["sigunguCd"], q["bjdongCd"]) == ("11680", "10500")


@respx.mock
async def test_service_timeout_is_retried():
    """이 API 는 503 SERVICETIMEOUT 을 자주 돌려준다 — 한 번에 포기하면 못 쓴다."""
    route = respx.get(url__startswith=BLD_BASE).mock(
        side_effect=[
            _xml(BLD_TIMEOUT_XML, status=503),
            _xml(BLD_TIMEOUT_XML, status=503),
            _xml(BLD_TITLE_XML),
        ]
    )
    async with MolitRealEstateAPIClient() as client:
        result = await client.get_building_register("11680", "10500", bun="1", ji="1")
    assert route.call_count == 3
    assert len(result["items"]) == 1


@respx.mock
async def test_persistent_timeout_raises():
    respx.get(url__startswith=BLD_BASE).mock(return_value=_xml(BLD_TIMEOUT_XML, status=503))
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(DataGoAPIError):
            await client.get_building_register("11680", "10500", bun="1", ji="1")


@respx.mock
async def test_missing_lot_is_an_empty_result():
    respx.get(url__startswith=BLD_BASE).mock(return_value=_xml(BLD_EMPTY_XML))
    async with MolitRealEstateAPIClient() as client:
        result = await client.get_building_register("11680", "10500", bun="9999", ji="9999")
    assert result == {"items": [], "total_count": 0}
