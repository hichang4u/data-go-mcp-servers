"""PpsNarajangteoAPIClient 테스트."""

import httpx
import pytest
import respx

from data_go_mcp.core.errors import DataGoAPIError
from data_go_mcp.pps_narajangteo.api_client import PpsNarajangteoAPIClient


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY")
    with pytest.raises(ValueError, match="API_KEY"):
        PpsNarajangteoAPIClient()


@respx.mock
async def test_get_bid_announcements_sends_expected_query(base_url, ok_response, bid_item):
    route = respx.get(f"{base_url}/getDataSetOpnStdBidPblancInfo").mock(
        return_value=httpx.Response(200, json=ok_response([bid_item], total=57))
    )

    async with PpsNarajangteoAPIClient() as client:
        body = await client.get_bid_announcements("202609010000", "202609122359", num_of_rows=5)

    q = route.calls.last.request.url.params
    assert q["serviceKey"] == "test-key"
    assert q["type"] == "json"
    assert q["bidNtceBgnDt"] == "202609010000"
    assert q["bidNtceEndDt"] == "202609122359"
    assert q["numOfRows"] == "5"
    assert q["pageNo"] == "1"

    assert body["totalCount"] == 57
    assert body["items"] == [bid_item]


@respx.mock
async def test_get_successful_bids_passes_business_div_and_opening_range(base_url, ok_response):
    route = respx.get(f"{base_url}/getDataSetOpnStdScsbidInfo").mock(
        return_value=httpx.Response(200, json=ok_response([]))
    )

    async with PpsNarajangteoAPIClient() as client:
        await client.get_successful_bids("3", "202609050000", "202609122359")

    q = route.calls.last.request.url.params
    assert q["bsnsDivCd"] == "3"
    assert q["opengBgnDt"] == "202609050000"
    assert q["opengEndDt"] == "202609122359"


@respx.mock
async def test_get_contracts_omits_none_filters(base_url, ok_response):
    route = respx.get(f"{base_url}/getDataSetOpnStdCntrctInfo").mock(
        return_value=httpx.Response(200, json=ok_response([]))
    )

    async with PpsNarajangteoAPIClient() as client:
        await client.get_contracts("20260901", "20260912", institution_div_code=None)

    q = route.calls.last.request.url.params
    assert q["cntrctCnclsBgnDate"] == "20260901"
    assert q["cntrctCnclsEndDate"] == "20260912"
    assert "insttDivCd" not in q
    assert "insttCd" not in q


@respx.mock
async def test_error_result_code_raises(base_url):
    respx.get(f"{base_url}/getDataSetOpnStdBidPblancInfo").mock(
        return_value=httpx.Response(
            200,
            json={
                "response": {
                    "header": {"resultCode": "07", "resultMsg": "입력범위값 초과"},
                    "body": {},
                }
            },
        )
    )
    async with PpsNarajangteoAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.get_bid_announcements("202601010000", "202612312359")
    assert exc.value.result_code == "07"
