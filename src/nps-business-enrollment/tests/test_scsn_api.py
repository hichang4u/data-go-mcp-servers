"""탈퇴사업장 클라이언트 테스트.

가입 사업장(``NpsBplcInfoInqireServiceV2``)과 같은 모양이지만 서비스가 다르고, 상세에
**탈퇴일(scsnDt)** 이 들어 있다. 사업자번호 제약도 같다 — 앞 6자리로만 걸리고 응답은 마스킹.
"""

import httpx
import pytest
import respx

from data_go_mcp.core import DataGoAPIError
from data_go_mcp.nps_business_enrollment.api_client import WithdrawnBusinessAPIClient

from .conftest import SCSN_BASE, SCSN_DETAIL_RESPONSE, SCSN_EMPTY_RESPONSE, SCSN_SEARCH_RESPONSE


@respx.mock
async def test_search_sends_camel_case_and_parses_items():
    route = respx.get(f"{SCSN_BASE}/getBassInfoSearchV2").mock(
        return_value=httpx.Response(200, json=SCSN_SEARCH_RESPONSE)
    )
    async with WithdrawnBusinessAPIClient() as client:
        result = await client.search_withdrawn_business(bzowr_rgst_no="119818", num_of_rows=2)

    params = route.calls.last.request.url.params
    assert params["bzowrRgstNo"] == "119818"
    assert params["numOfRows"] == "2"

    first = result["items"][0]
    assert first["wkpl_nm"]
    assert first["bzowr_rgst_no"].endswith("****")  # 뒷자리는 마스킹돼 온다
    assert first["seq"]
    assert result["total_count"] > 0


@respx.mock
async def test_detail_exposes_the_withdrawal_date():
    """탈퇴일이 이 API 를 쓰는 이유다."""
    route = respx.get(f"{SCSN_BASE}/getDetailInfoSearchV2").mock(
        return_value=httpx.Response(200, json=SCSN_DETAIL_RESPONSE)
    )
    async with WithdrawnBusinessAPIClient() as client:
        result = await client.get_withdrawn_business_detail(seq=1473020)

    assert route.calls.last.request.url.params["seq"] == "1473020"
    first = result["items"][0]
    assert first["scsn_dt"] == "20260501"
    assert first["acpt_dt"] == "20260119"
    assert first["vldt_vl_krn_nm"] == "미장, 타일 및 방수 공사업"


@respx.mock
async def test_no_match_is_an_empty_result():
    """items 가 빈 dict 로 온다 — 리스트가 아니다."""
    respx.get(url__startswith=SCSN_BASE).mock(
        return_value=httpx.Response(200, json=SCSN_EMPTY_RESPONSE)
    )
    async with WithdrawnBusinessAPIClient() as client:
        result = await client.search_withdrawn_business(wkpl_nm="없는회사")
    assert result["items"] == []
    assert result["total_count"] == 0


async def test_search_needs_a_filter():
    """조건 없이 부르면 API 가 0건을 준다 — 미리 막아 혼란을 줄인다."""
    async with WithdrawnBusinessAPIClient() as client:
        with pytest.raises(ValueError, match="사업장명|사업자번호"):
            await client.search_withdrawn_business()


@pytest.mark.parametrize("value", ["1208800767", "12081", "abcdef"])
async def test_business_number_must_be_the_first_six_digits(value):
    """10자리를 그대로 보내면 조용히 0건이 온다 (실호출 확인)."""
    async with WithdrawnBusinessAPIClient() as client:
        with pytest.raises(ValueError, match="앞 6자리"):
            await client.search_withdrawn_business(bzowr_rgst_no=value)


@respx.mock
async def test_api_error_is_raised():
    respx.get(url__startswith=SCSN_BASE).mock(
        return_value=httpx.Response(
            200,
            json={"response": {"header": {"resultCode": "30", "resultMsg": "NOT REGISTERED"}}},
        )
    )
    async with WithdrawnBusinessAPIClient() as client:
        with pytest.raises(DataGoAPIError):
            await client.search_withdrawn_business(wkpl_nm="쿠팡")


async def test_shares_the_server_key_prefix():
    """같은 서버의 다른 클라이언트들과 키를 공유한다 (설정 항목을 늘리지 않는다)."""
    assert WithdrawnBusinessAPIClient.key_env_prefix == "NPS_BUSINESS_ENROLLMENT"
    assert WithdrawnBusinessAPIClient.shared_key is True


@respx.mock
async def test_region_only_search_is_allowed():
    """지역만으로도 API 는 답한다 — 실측 41/590 → 29,050건. 가드가 막으면 안 된다."""
    route = respx.get(f"{SCSN_BASE}/getBassInfoSearchV2").mock(
        return_value=httpx.Response(200, json=SCSN_SEARCH_RESPONSE)
    )
    async with WithdrawnBusinessAPIClient() as client:
        await client.search_withdrawn_business(
            ldong_addr_mgpl_dg_cd="41", ldong_addr_mgpl_sggu_cd="590"
        )
    params = route.calls.last.request.url.params
    assert params["ldongAddrMgplDgCd"] == "41"
    assert params["ldongAddrMgplSgguCd"] == "590"


@respx.mock
async def test_emd_code_reaches_the_api():
    route = respx.get(f"{SCSN_BASE}/getBassInfoSearchV2").mock(
        return_value=httpx.Response(200, json=SCSN_SEARCH_RESPONSE)
    )
    async with WithdrawnBusinessAPIClient() as client:
        await client.search_withdrawn_business(
            ldong_addr_mgpl_dg_cd="41",
            ldong_addr_mgpl_sggu_cd="590",
            ldong_addr_mgpl_sggu_emd_cd="101",
        )
    assert route.calls.last.request.url.params["ldongAddrMgplSgguEmdCd"] == "101"


@respx.mock
async def test_blank_business_number_is_treated_as_absent():
    """빈 문자열을 넣는 클라이언트가 있다 — 이름 검색을 막으면 안 된다."""
    route = respx.get(f"{SCSN_BASE}/getBassInfoSearchV2").mock(
        return_value=httpx.Response(200, json=SCSN_SEARCH_RESPONSE)
    )
    async with WithdrawnBusinessAPIClient() as client:
        await client.search_withdrawn_business(wkpl_nm="쿠팡", bzowr_rgst_no="")
    assert route.calls.last.request.url.params["wkplNm"] == "쿠팡"
