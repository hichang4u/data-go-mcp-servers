"""StockPriceAPIClient(주식시세정보) 테스트. HTTP 는 respx, 응답은 실응답 발췌."""

import httpx
import pytest
import respx

from data_go_mcp.fsc_financial_info.api_client import StockPriceAPIClient


@respx.mock
async def test_get_stock_prices_by_name_parses_numbers(stock_base_url, stock_response):
    route = respx.get(f"{stock_base_url}/getStockPriceInfo_V2").mock(
        return_value=httpx.Response(200, json=stock_response)
    )
    async with StockPriceAPIClient() as client:
        result = await client.get_stock_prices(itms_nm="삼성전자", num_of_rows=2)

    params = route.calls.last.request.url.params
    assert params["itmsNm"] == "삼성전자"
    assert params["resultType"] == "json"
    assert "likeSrtnCd" not in params and "isinCd" not in params

    assert result["total_count"] == 1643
    first = result["items"][0]
    assert first["bas_dt"] == "20260910"
    assert first["srtn_cd"] == "005930"
    assert first["isin_cd"] == "KR7005930003"
    assert first["mrkt_ctg"] == "KOSPI"
    assert first["clpr"] == 269000
    assert first["vs"] == -500
    assert first["flt_rt"] == -0.19
    assert first["trqu"] == 22517075
    assert first["mrkt_tot_amt"] == 1572648945552000


@respx.mock
async def test_get_stock_prices_by_code_and_date_range(stock_base_url, stock_response):
    route = respx.get(f"{stock_base_url}/getStockPriceInfo_V2").mock(
        return_value=httpx.Response(200, json=stock_response)
    )
    async with StockPriceAPIClient() as client:
        await client.get_stock_prices(
            srtn_cd="005930", begin_bas_dt="2026-09-01", end_bas_dt="20260910"
        )

    params = route.calls.last.request.url.params
    assert params["likeSrtnCd"] == "005930"
    assert params["beginBasDt"] == "20260901"
    assert params["endBasDt"] == "20260910"


async def test_get_stock_prices_requires_an_identifier():
    async with StockPriceAPIClient() as client:
        with pytest.raises(ValueError, match="종목명"):
            await client.get_stock_prices(bas_dt="20260910")


@pytest.mark.parametrize("kwargs", [{"srtn_cd": "5930"}, {"bas_dt": "2026091"}])
async def test_get_stock_prices_rejects_bad_formats(kwargs):
    async with StockPriceAPIClient() as client:
        with pytest.raises(ValueError):
            await client.get_stock_prices(itms_nm="삼성전자", **kwargs)


@respx.mock
async def test_search_items_lists_distinct_items_as_of_latest_date(
    stock_base_url, stock_search_responses
):
    probe, listing = stock_search_responses
    route = respx.get(f"{stock_base_url}/getStockPriceInfo_V2").mock(
        side_effect=[httpx.Response(200, json=probe), httpx.Response(200, json=listing)]
    )
    async with StockPriceAPIClient() as client:
        result = await client.search_items("삼성", num_of_rows=50)

    first, second = (c.request.url.params for c in route.calls)
    assert first["likeItmsNm"] == "삼성" and first["numOfRows"] == "1"
    assert second["likeItmsNm"] == "삼성" and second["basDt"] == "20260910"
    assert second["numOfRows"] == "50"

    assert result["bas_dt"] == "20260910"
    assert result["total_count"] == 26
    assert [i["itms_nm"] for i in result["items"]] == ["삼성화재", "삼성화재우"]


@respx.mock
async def test_search_items_no_match(stock_base_url, stock_empty_response):
    route = respx.get(f"{stock_base_url}/getStockPriceInfo_V2").mock(
        return_value=httpx.Response(200, json=stock_empty_response)
    )
    async with StockPriceAPIClient() as client:
        result = await client.search_items("없는종목")

    assert route.call_count == 1
    assert result == {"bas_dt": None, "items": [], "total_count": 0}
