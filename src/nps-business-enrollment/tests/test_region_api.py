"""RegionCodeAPIClient(법정동코드) 테스트. HTTP 는 respx, 응답은 실응답 발췌."""

import httpx
import pytest
import respx

from data_go_mcp.core.errors import DataGoAPIError
from data_go_mcp.nps_business_enrollment.api_client import RegionCodeAPIClient


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")


@respx.mock
async def test_search_region_sends_name_and_parses_rows(region_base_url, region_response):
    route = respx.get(f"{region_base_url}/getStanReginCdList").mock(
        return_value=httpx.Response(200, json=region_response)
    )
    async with RegionCodeAPIClient() as client:
        result = await client.search_region("강남구", page_no=1, num_of_rows=3)

    params = route.calls.last.request.url.params
    assert params["locatadd_nm"] == "강남구"
    assert params["type"] == "json"
    assert params["pageNo"] == "1"
    assert params["numOfRows"] == "3"
    assert params["serviceKey"] == "test-key"

    assert result["total_count"] == 15
    assert result["page_no"] == 1
    assert result["num_of_rows"] == 3
    first = result["items"][0]
    assert first["region_cd"] == "1168010100"
    assert first["name"] == "서울특별시 강남구 역삼동"
    assert (first["sido_cd"], first["sgg_cd"], first["umd_cd"], first["ri_cd"]) == (
        "11",
        "680",
        "101",
        "00",
    )
    assert first["parent_cd"] == "1168000000"


@respx.mock
async def test_no_data_result_gives_empty_list(region_base_url, region_no_data_response):
    respx.get(f"{region_base_url}/getStanReginCdList").mock(
        return_value=httpx.Response(200, json=region_no_data_response)
    )
    async with RegionCodeAPIClient() as client:
        result = await client.search_region("없는동네")

    assert result["items"] == []
    assert result["total_count"] == 0


@respx.mock
async def test_other_result_code_raises_data_go_error(region_base_url):
    respx.get(f"{region_base_url}/getStanReginCdList").mock(
        return_value=httpx.Response(
            200, json={"RESULT": {"resultCode": "ERROR-300", "resultMsg": "필수 값이 누락"}}
        )
    )
    async with RegionCodeAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.search_region("")

    assert exc.value.result_code == "ERROR-300"
