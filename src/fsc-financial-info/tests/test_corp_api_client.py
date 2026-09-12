"""CorpBasicInfoAPIClient(기업기본정보) 테스트. HTTP 는 respx, 응답은 실응답 발췌."""

import httpx
import pytest
import respx

from data_go_mcp.fsc_financial_info.api_client import CorpBasicInfoAPIClient


@respx.mock
async def test_search_by_name_dedupes_snapshots_keeping_latest(
    corp_base_url, corp_response
):
    route = respx.get(f"{corp_base_url}/getCorpOutline_V2").mock(
        return_value=httpx.Response(200, json=corp_response)
    )
    async with CorpBasicInfoAPIClient() as client:
        result = await client.search_corporations(
            corp_name="삼성전자(주)", num_of_rows=50
        )

    params = route.calls.last.request.url.params
    assert params["corpNm"] == "삼성전자(주)"
    assert params["resultType"] == "json"
    assert params["numOfRows"] == "50"
    assert "bzno" not in params and "crno" not in params

    assert result["total_count"] == 20  # 스냅샷 건수 (API 의 totalCount)
    assert [c["crno"] for c in result["items"]] == ["1301110006246", "2845110008637"]
    samsung = result["items"][0]
    assert samsung["corp_nm"] == "삼성전자(주)"
    assert samsung["bzno"] == "1248100998"
    assert samsung["market"] == "유가"
    assert samsung["snapshot_dt"] == "20260911"
    assert samsung["actn_audpn_nm"] == "삼정회계법인"  # 최신 스냅샷의 값


@respx.mock
async def test_search_by_bzno_strips_hyphens(corp_base_url, corp_response):
    route = respx.get(f"{corp_base_url}/getCorpOutline_V2").mock(
        return_value=httpx.Response(200, json=corp_response)
    )
    async with CorpBasicInfoAPIClient() as client:
        await client.search_corporations(bzno="124-81-00998")

    assert route.calls.last.request.url.params["bzno"] == "1248100998"


@pytest.mark.parametrize("bzno", ["12481", "124-81-0099A"])
async def test_search_rejects_bad_bzno(bzno):
    async with CorpBasicInfoAPIClient() as client:
        with pytest.raises(ValueError, match="사업자등록번호"):
            await client.search_corporations(bzno=bzno)


async def test_search_requires_name_or_bzno():
    async with CorpBasicInfoAPIClient() as client:
        with pytest.raises(ValueError):
            await client.search_corporations()


@respx.mock
async def test_get_corp_outline_returns_latest_snapshot(corp_base_url, corp_response):
    route = respx.get(f"{corp_base_url}/getCorpOutline_V2").mock(
        return_value=httpx.Response(200, json=corp_response)
    )
    async with CorpBasicInfoAPIClient() as client:
        outline = await client.get_corp_outline("130111-0006246")

    assert route.calls.last.request.url.params["crno"] == "1301110006246"
    assert outline is not None
    assert outline["crno"] == "1301110006246"
    assert outline["snapshot_dt"] == "20260911"
    assert outline["enp_empe_cnt"] == 128881
    assert outline["enp_pn1_avg_slry_amt"] == 158000000
    assert outline["audt_rpt_opnn_ctt"] == "적정의견"


@respx.mock
async def test_get_corp_outline_none_when_empty(corp_base_url, empty_response):
    respx.get(f"{corp_base_url}/getCorpOutline_V2").mock(
        return_value=httpx.Response(200, json=empty_response)
    )
    async with CorpBasicInfoAPIClient() as client:
        assert await client.get_corp_outline("1301110006246") is None


async def test_get_corp_outline_rejects_bad_crno():
    async with CorpBasicInfoAPIClient() as client:
        with pytest.raises(ValueError, match="법인등록번호"):
            await client.get_corp_outline("12345")
