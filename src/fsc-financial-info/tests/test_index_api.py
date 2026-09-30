"""지수시세·증권상품시세 클라이언트 테스트 (2026-09-29 실응답 기준)."""

import httpx
import pytest
import respx

from data_go_mcp.fsc_financial_info.api_client import (
    MarketIndexAPIClient,
    SecuritiesProductAPIClient,
)


@respx.mock
async def test_stock_index_normalizes_numbers(index_base_url, stock_index_response):
    route = respx.get(f"{index_base_url}/getStockMarketIndex_V2").mock(
        return_value=httpx.Response(200, json=stock_index_response)
    )
    async with MarketIndexAPIClient() as client:
        result = await client.get_indices(index_name="코스피", begin_bas_dt="20260925")

    q = route.calls.last.request.url.params
    assert q["idxNm"] == "코스피" and q["beginBasDt"] == "20260925"

    first = result["items"][0]
    assert first["index_name"] == "코스피"
    assert first["close"] == 6889.74
    assert first["change"] == -191.18
    assert first["change_rate"] == -2.7
    assert first["listed_market_cap"] == 5689659864797724
    assert first["component_count"] == 828
    assert result["total_count"] == 1654


@respx.mock
async def test_partial_index_name_uses_like_param(index_base_url, stock_index_response):
    route = respx.get(url__startswith=index_base_url).mock(
        return_value=httpx.Response(200, json=stock_index_response)
    )
    async with MarketIndexAPIClient() as client:
        await client.get_indices(like_index_name="코스피")

    q = route.calls.last.request.url.params
    assert q["likeIdxNm"] == "코스피" and "idxNm" not in q


@respx.mock
async def test_bond_index_keeps_its_own_fields(index_base_url, bond_index_response):
    route = respx.get(f"{index_base_url}/getBondMarketIndex_V2").mock(
        return_value=httpx.Response(200, json=bond_index_response)
    )
    async with MarketIndexAPIClient() as client:
        result = await client.get_indices(index_type="채권", bas_dt="20260929")

    assert route.called
    first = result["items"][0]
    assert first["index_name"] == "KRX 채권지수"
    assert first["total_return_index"] == 194.21
    assert first["duration"] == 4.835
    assert first["ytm"] == 4.318


async def test_unknown_index_type_is_rejected():
    async with MarketIndexAPIClient() as client:
        with pytest.raises(ValueError, match="지수 종류"):
            await client.get_indices(index_type="파생")


@respx.mock
async def test_etf_price_normalizes_nav(product_base_url, etf_response):
    route = respx.get(f"{product_base_url}/getETFPriceInfo_V2").mock(
        return_value=httpx.Response(200, json=etf_response)
    )
    async with SecuritiesProductAPIClient() as client:
        result = await client.get_product_prices(
            like_item_name="KODEX 200", bas_dt="20260929"
        )

    q = route.calls.last.request.url.params
    assert q["likeItmsNm"] == "KODEX 200"

    first = result["items"][0]
    assert first["item_name"] == "KODEX 200커버드콜액티브"
    assert first["short_code"] == "0219E0"
    assert first["close"] == 8295
    assert first["nav"] == 8296.09
    assert first["base_index_name"] == "코스피 200 커버드콜 5% OTM"
    assert first["listed_count"] == 110800000


@respx.mock
async def test_etn_uses_indicative_value(product_base_url, etn_response):
    route = respx.get(f"{product_base_url}/getETNPriceInfo_V2").mock(
        return_value=httpx.Response(200, json=etn_response)
    )
    async with SecuritiesProductAPIClient() as client:
        result = await client.get_product_prices(product_type="ETN", bas_dt="20260929")

    assert route.called
    first = result["items"][0]
    assert first["indicative_value"] == 9431.81
    assert first["nav"] is None
    assert first["listed_count"] == 700000


async def test_unknown_product_type_is_rejected():
    async with SecuritiesProductAPIClient() as client:
        with pytest.raises(ValueError, match="상품 종류"):
            await client.get_product_prices(product_type="ELW")


@respx.mock
async def test_short_code_uses_like_param(product_base_url, etf_response):
    """단축코드가 ETF 는 ``0219E0`` 처럼 영숫자 6자리다 — 주식의 숫자 6자리 검증과 다르다."""
    route = respx.get(url__startswith=product_base_url).mock(
        return_value=httpx.Response(200, json=etf_response)
    )
    async with SecuritiesProductAPIClient() as client:
        await client.get_product_prices(short_code="0219E0")

    assert route.calls.last.request.url.params["likeSrtnCd"] == "0219E0"


@respx.mock
async def test_empty_result_is_not_an_error(index_base_url, stock_empty_response):
    respx.get(url__startswith=index_base_url).mock(
        return_value=httpx.Response(200, json=stock_empty_response)
    )
    async with MarketIndexAPIClient() as client:
        result = await client.get_indices(index_name="없는지수")
    assert result["items"] == [] and result["total_count"] == 0


@pytest.mark.parametrize("rows", [0, 101, 99999])
async def test_index_row_count_is_capped_like_other_clients(rows):
    """다른 클라이언트와 같은 한도(1~100)를 지켜야 한 번에 수십만 건을 끌어오지 않는다."""
    async with MarketIndexAPIClient() as client:
        with pytest.raises(ValueError):
            await client.get_indices(index_name="코스피", num_of_rows=rows)


async def test_product_row_count_is_capped():
    async with SecuritiesProductAPIClient() as client:
        with pytest.raises(ValueError):
            await client.get_product_prices(like_item_name="KODEX", num_of_rows=99999)


async def test_page_no_must_be_positive():
    async with MarketIndexAPIClient() as client:
        with pytest.raises(ValueError):
            await client.get_indices(index_name="코스피", page_no=0)


async def test_date_errors_name_the_offending_parameter():
    """세 날짜가 같은 이름으로 보고되면 어느 것이 틀렸는지 알 수 없다."""
    async with MarketIndexAPIClient() as client:
        with pytest.raises(ValueError, match="begin_bas_dt|시작"):
            await client.get_indices(
                index_name="코스피", bas_dt="20260929", begin_bas_dt="2026-09"
            )
        with pytest.raises(ValueError, match="end_bas_dt|끝"):
            await client.get_indices(index_name="코스피", end_bas_dt="2026")


@respx.mock
async def test_index_result_reports_page_size(index_base_url, stock_index_response):
    """total_count 만으로는 페이지 수를 계산할 수 없다 — 다른 툴처럼 num_of_rows 를 돌려준다."""
    respx.get(url__startswith=index_base_url).mock(
        return_value=httpx.Response(200, json=stock_index_response)
    )
    async with MarketIndexAPIClient() as client:
        result = await client.get_indices(index_name="코스피", num_of_rows=5)
    assert result["num_of_rows"] == 5
