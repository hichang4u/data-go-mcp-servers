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


@respx.mock
async def test_house_price_kind_carries_the_price():
    """주택가격은 공시가격이 전부인데 모델에 가격 필드가 없으면 빈 행만 나온다."""
    from .conftest import BLD_HSPRC_XML

    respx.get(f"{BLD_BASE}/getBrHsprcInfo").mock(return_value=_xml(BLD_HSPRC_XML))
    async with MolitRealEstateAPIClient() as client:
        result = await client.get_building_register("1168011000", bun="493", kind="주택가격")
    first = result["items"][0]
    assert first["house_price"] == 3344000000
    assert first["price_base_date"] == "2024-01-01"
    assert first["building_name"] == "영동한양아파트 제25동"


@respx.mock
async def test_exclusive_area_kind_identifies_the_unit():
    """전유/공용 구분과 호 이름이 없으면 어느 집의 면적인지 알 수 없다."""
    from .conftest import BLD_EXPOS_XML

    respx.get(f"{BLD_BASE}/getBrExposPubuseAreaInfo").mock(return_value=_xml(BLD_EXPOS_XML))
    async with MolitRealEstateAPIClient() as client:
        result = await client.get_building_register("1168011000", bun="493", kind="전유공용면적")
    first = result["items"][0]
    assert first["unit_name"] == "103호"
    assert first["area_type"] == "전유"
    assert first["area"] == 147.41
    assert first["main_purpose"] == "아파트"


@respx.mock
async def test_title_exposes_the_parking_counts_it_actually_has():
    """표제부에는 totPkngCnt 가 없고 자주식·기계식 네 칸이 온다."""
    respx.get(url__startswith=BLD_BASE).mock(return_value=_xml(BLD_TITLE_XML))
    async with MolitRealEstateAPIClient() as client:
        result = await client.get_building_register("11680", "10500", bun="1", ji="1")
    first = result["items"][0]
    assert first["indoor_self_parking"] == 33
    assert first["outdoor_self_parking"] == 27


async def test_sido_level_code_is_rejected_here_too():
    """시도 코드를 보내면 bjdongCd=00000 이 되어 조용히 0건이 온다."""
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(ValueError, match="시군구"):
            await client.get_building_register("1100000000", bun="1")


async def test_conflicting_bjdong_code_is_rejected():
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(ValueError, match="법정동"):
            await client.get_building_register("1168011000", bjdong_code="10500", bun="1")


@respx.mock
async def test_retries_enough_times_for_this_api(monkeypatch):
    """3회로는 실호출에서 실패했다 (2026-10-01 압구정동 표제부). 기다림은 테스트에서 건너뛴다."""
    slept: list[float] = []

    async def no_wait(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr("data_go_mcp.molit_realestate.api_client.asyncio.sleep", no_wait)
    route = respx.get(url__startswith=BLD_BASE).mock(
        side_effect=[_xml(BLD_TIMEOUT_XML, status=503)] * 4 + [_xml(BLD_TITLE_XML)]
    )
    async with MolitRealEstateAPIClient() as client:
        result = await client.get_building_register("11680", "10500", bun="1", ji="1")

    assert route.call_count == 5
    assert len(result["items"]) == 1
    assert slept == sorted(slept) and slept[-1] > slept[0]  # 점점 길게 기다린다


@respx.mock
async def test_exhausted_retries_say_it_is_overload(monkeypatch):
    """[05] SERVICETIMEOUT 만 보면 뭘 해야 할지 알 수 없다."""

    async def no_wait(seconds: float) -> None:
        return None

    monkeypatch.setattr("data_go_mcp.molit_realestate.api_client.asyncio.sleep", no_wait)
    respx.get(url__startswith=BLD_BASE).mock(return_value=_xml(BLD_TIMEOUT_XML, status=503))
    async with MolitRealEstateAPIClient() as client:
        with pytest.raises(DataGoAPIError, match="다시 시도"):
            await client.get_building_register("11680", "10500", bun="1", ji="1")
