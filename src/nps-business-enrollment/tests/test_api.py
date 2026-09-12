"""NPSAPIClient 테스트. HTTP는 respx로 가로채고 응답은 S0b에서 받은 실제 형태를 쓴다."""

import httpx
import pytest
import respx

from data_go_mcp.core.errors import DataGoAPIError
from data_go_mcp.nps_business_enrollment.api_client import NPSAPIClient


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("NPS_BUSINESS_ENROLLMENT_API_KEY", raising=False)


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY")
    with pytest.raises(ValueError, match="API_KEY"):
        NPSAPIClient()


@respx.mock
async def test_search_business_sends_camel_case_params_and_parses_items(base_url, search_response):
    route = respx.get(f"{base_url}/getBassInfoSearchV2").mock(
        return_value=httpx.Response(200, json=search_response)
    )

    async with NPSAPIClient() as client:
        result = await client.search_business(wkpl_nm="삼성전자", bzowr_rgst_no=None)

    q = route.calls.last.request.url.params
    assert q["serviceKey"] == "test-key"
    assert q["dataType"] == "json"
    assert q["wkplNm"] == "삼성전자"
    assert q["numOfRows"] == "100"
    assert "bzowrRgstNo" not in q

    assert result["total_count"] == 2107
    assert result["page_no"] == 1
    assert result["items"] == [
        {
            "data_crt_ym": "202607",
            "seq": 7101020,
            "wkpl_nm": "주식회사 유일이엔지",
            "bzowr_rgst_no": "142816****",
            "wkpl_road_nm_dtl_addr": "경기도 평택시 삼성로",
            "wkpl_jnng_stcd": "1",
            "wkpl_styl_dvcd": "1",
            "ldong_addr_mgpl_dg_cd": "41",
            "ldong_addr_mgpl_sggu_cd": "220",
            "ldong_addr_mgpl_sggu_emd_cd": "128",
        }
    ]


@respx.mock
async def test_get_business_detail_parses_subscriber_fields(base_url, detail_response):
    respx.get(f"{base_url}/getDetailInfoSearchV2").mock(
        return_value=httpx.Response(200, json=detail_response)
    )

    async with NPSAPIClient() as client:
        result = await client.get_business_detail(seq=7101020)

    item = result["items"][0]
    assert item["jnngp_cnt"] == 36
    assert item["crrmm_ntc_amt"] == "7979660"
    assert item["vldt_vl_krn_nm"] == "배관 및 냉ㆍ난방 공사업"


@respx.mock
async def test_get_period_status_passes_data_crt_ym(base_url, period_response):
    route = respx.get(f"{base_url}/getPdAcctoSttusInfoSearchV2").mock(
        return_value=httpx.Response(200, json=period_response)
    )

    async with NPSAPIClient() as client:
        result = await client.get_period_status(seq=7101020, data_crt_ym="202607")

    assert route.calls.last.request.url.params["dataCrtYm"] == "202607"
    assert result["items"] == [{"nw_acqzr_cnt": 36, "lss_jnngp_cnt": 7}]


@respx.mock
async def test_empty_items_gives_empty_list(base_url):
    respx.get(f"{base_url}/getBassInfoSearchV2").mock(
        return_value=httpx.Response(
            200,
            json={
                "response": {
                    "header": {"resultCode": "00", "resultMsg": "NORMAL_CODE"},
                    "body": {"items": "", "pageNo": 1, "numOfRows": 100, "totalCount": 0},
                }
            },
        )
    )
    async with NPSAPIClient() as client:
        result = await client.search_business(wkpl_nm="없는회사")

    assert result["items"] == []
    assert result["total_count"] == 0


@respx.mock
async def test_error_result_code_raises_data_go_error(base_url):
    respx.get(f"{base_url}/getBassInfoSearchV2").mock(
        return_value=httpx.Response(
            200,
            json={
                "response": {"header": {"resultCode": "22", "resultMsg": "LIMITED"}, "body": {}}
            },
        )
    )
    async with NPSAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.search_business(wkpl_nm="x")
    assert exc.value.result_code == "22"
