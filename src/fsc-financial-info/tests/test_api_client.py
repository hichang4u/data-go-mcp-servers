"""FSCFinancialAPIClient 테스트."""

from decimal import Decimal

import httpx
import pytest
import respx
from data_go_mcp.core.errors import DataGoAPIError

from data_go_mcp.fsc_financial_info.api_client import (
    FSCFinancialAPIClient,
    parse_decimal,
)


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY")
    with pytest.raises(ValueError, match="API_KEY"):
        FSCFinancialAPIClient()


def test_prefixed_key_wins(monkeypatch):
    monkeypatch.setenv("FSC_FINANCIAL_INFO_API_KEY", "fsc-key")
    assert FSCFinancialAPIClient().api_key == "fsc-key"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("12345.67", Decimal("12345.67")),
        ("12,345.67", Decimal("12345.67")),
        ("-12345", Decimal("-12345")),
        ("", None),
        (None, None),
        ("invalid", None),
    ],
)
def test_parse_decimal(raw, expected):
    assert parse_decimal(raw) == expected


@respx.mock
async def test_get_summary_financial_statement(base_url, summary_response):
    route = respx.get(f"{base_url}/getSummFinaStat_V2").mock(
        return_value=httpx.Response(200, json=summary_response)
    )
    async with FSCFinancialAPIClient() as client:
        resp = await client.get_summary_financial_statement(
            crno="1301110006246", biz_year="2023"
        )

    q = route.calls.last.request.url.params
    assert q["serviceKey"] == "test-key"
    assert q["resultType"] == "json"
    assert q["crno"] == "1301110006246"
    assert q["bizYear"] == "2023"

    assert resp.total_count == 2
    item = resp.items[0]
    assert item.fncl_dcd_nm == "연결요약재무제표"
    assert item.enp_sale_amt == Decimal("258935494000000")
    assert item.fncl_debt_rto == Decimal("25.3598373385")


@respx.mock
async def test_get_balance_sheet(base_url, balance_response):
    respx.get(f"{base_url}/getBs_V2").mock(
        return_value=httpx.Response(200, json=balance_response)
    )
    async with FSCFinancialAPIClient() as client:
        resp = await client.get_balance_sheet(crno="1301110006246", biz_year="2023")

    assert resp.total_count == 18
    assert resp.items[0].acit_nm == "자산총계"
    assert resp.items[0].crtm_acit_amt == Decimal("455905980000000")
    assert resp.items[0].pvtr_acit_amt == Decimal("448424507000000")


@respx.mock
async def test_get_income_statement(base_url, income_response):
    respx.get(f"{base_url}/getIncoStat_V2").mock(
        return_value=httpx.Response(200, json=income_response)
    )
    async with FSCFinancialAPIClient() as client:
        resp = await client.get_income_statement(crno="1301110006246", biz_year="2023")

    assert resp.items[0].acit_id == "dart_OperatingIncomeLoss"
    assert resp.items[0].crtm_acit_amt == Decimal("6566976000000")


@respx.mock
async def test_empty_items(base_url, empty_response):
    respx.get(f"{base_url}/getSummFinaStat_V2").mock(
        return_value=httpx.Response(200, json=empty_response)
    )
    async with FSCFinancialAPIClient() as client:
        resp = await client.get_summary_financial_statement(
            crno="9999999999999", biz_year="2023"
        )
    assert resp.items == []
    assert resp.total_count == 0


async def test_invalid_crno_is_value_error():
    async with FSCFinancialAPIClient() as client:
        with pytest.raises(ValueError, match="13자리"):
            await client.get_summary_financial_statement(crno="123", biz_year="2023")


@respx.mock
async def test_api_error_raises(base_url):
    respx.get(f"{base_url}/getSummFinaStat_V2").mock(
        return_value=httpx.Response(
            200,
            json={
                "response": {
                    "header": {"resultCode": "30", "resultMsg": "KEY"},
                    "body": {},
                }
            },
        )
    )
    async with FSCFinancialAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.get_summary_financial_statement()
    assert exc.value.result_code == "30"
