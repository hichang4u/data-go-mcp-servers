"""NtsBusinessVerificationAPIClient 테스트 (odcloud: POST JSON, status_code/data 구조)."""

import json

import httpx
import pytest
import respx

from data_go_mcp.core.errors import DataGoAPIError
from data_go_mcp.nts_business_verification.api_client import NtsBusinessVerificationAPIClient
from data_go_mcp.nts_business_verification.models import BusinessInfo


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY")
    with pytest.raises(ValueError, match="API_KEY"):
        NtsBusinessVerificationAPIClient()


@respx.mock
async def test_check_status_posts_cleaned_numbers(base_url, status_response):
    route = respx.post(f"{base_url}/status").mock(
        return_value=httpx.Response(200, json=status_response)
    )
    async with NtsBusinessVerificationAPIClient() as client:
        resp = await client.check_status(["120-88-00767", "0000000000"])

    req = route.calls.last.request
    assert req.url.params["serviceKey"] == "test-key"
    assert req.url.params["returnType"] == "JSON"
    assert json.loads(req.content) == {"b_no": ["1208800767", "0000000000"]}

    assert resp.status_code == "OK"
    assert resp.match_cnt == 1
    assert resp.data[0].b_stt_cd == "01"
    assert resp.data[1].tax_type == "국세청에 등록되지 않은 사업자등록번호입니다."


@respx.mock
async def test_validate_business_sends_all_fields_with_blanks(base_url, validate_mismatch):
    route = respx.post(f"{base_url}/validate").mock(
        return_value=httpx.Response(200, json=validate_mismatch)
    )
    async with NtsBusinessVerificationAPIClient() as client:
        resp = await client.validate_business(
            [BusinessInfo(b_no="1208800767", start_dt="20000101", p_nm="홍길동")]
        )

    sent = json.loads(route.calls.last.request.content)["businesses"][0]
    assert sent == {
        "b_no": "1208800767",
        "start_dt": "20000101",
        "p_nm": "홍길동",
        "p_nm2": "",
        "b_nm": "",
        "corp_no": "",
        "b_sector": "",
        "b_type": "",
        "b_adr": "",
    }
    assert resp.data[0].valid == "02"
    assert resp.data[0].status is None


@respx.mock
async def test_validate_match_includes_status(base_url, validate_match):
    respx.post(f"{base_url}/validate").mock(return_value=httpx.Response(200, json=validate_match))
    async with NtsBusinessVerificationAPIClient() as client:
        resp = await client.validate_business(
            [BusinessInfo(b_no="1208800767", start_dt="20000101", p_nm="홍길동")]
        )
    assert resp.valid_cnt == 1
    assert resp.data[0].status is not None
    assert resp.data[0].status.b_stt == "계속사업자"


async def test_more_than_100_is_rejected_before_request():
    async with NtsBusinessVerificationAPIClient() as client:
        with pytest.raises(ValueError, match="100"):
            await client.check_status(["1234567890"] * 101)


@respx.mock
async def test_non_ok_status_code_raises_data_go_error(base_url):
    respx.post(f"{base_url}/status").mock(
        return_value=httpx.Response(
            200, json={"status_code": "BAD_JSON_REQUEST", "msg": "잘못된 요청"}
        )
    )
    async with NtsBusinessVerificationAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.check_status(["1208800767"])
    assert exc.value.result_code == "BAD_JSON_REQUEST"


@respx.mock
async def test_unauthorized_key_raises_data_go_error(base_url):
    # S0b 에서 관측한 odcloud 401 형태
    respx.post(f"{base_url}/status").mock(
        return_value=httpx.Response(
            401, json={"code": -401, "msg": "유효하지 않은 인증키 입니다."}
        )
    )
    async with NtsBusinessVerificationAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.check_status(["1208800767"])
    assert exc.value.result_code == "-401"
    assert "유효하지 않은 인증키" in exc.value.result_msg
