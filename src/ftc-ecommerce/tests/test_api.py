"""통신판매사업자 클라이언트 테스트.

이 API 의 두 함정을 테스트로 못박는다 — 빈 값이 ``"N/A"`` 문자열로 오는 것,
그리고 상호 파라미터가 무시되어 전체 276만 건이 돌아오는 것.
"""

import httpx
import pytest
import respx

from data_go_mcp.core import DataGoAPIError
from data_go_mcp.ftc_ecommerce.api_client import FtcEcommerceAPIClient

from .conftest import BASE, CLOSED_RESPONSE, EMPTY_RESPONSE, SELLER_RESPONSE


ENDPOINT = f"{BASE}/getMllBsInfoDetail_3"


@respx.mock
async def test_lookup_by_business_number():
    route = respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json=SELLER_RESPONSE))
    async with FtcEcommerceAPIClient() as client:
        result = await client.get_online_seller("120-88-00767")

    params = route.calls.last.request.url.params
    assert params["brno"] == "1208800767"  # 하이픈을 떼고 보낸다
    assert params["resultType"] == "json"

    seller = result["items"][0]
    assert seller["name"] == "쿠팡주식회사"
    assert seller["business_number"] == "1208800767"
    assert seller["corporate_number"] == "1101115067718"
    assert seller["representative"] == "김범석,로저스 해롤드 린(Rogers Harold Lynn)"
    assert seller["corporation"] is True
    assert seller["operating_status"] == "정상영업"
    assert seller["business_status"] == "계속사업자"
    assert seller["report_number"] == "2026-서울광진-1253"
    assert seller["reported_on"] == "2013-08-21"
    assert seller["reported_to"] == "서울특별시 광진구"
    assert seller["sales_method"] == "인터넷"
    assert seller["product_type"] == "종합몰"
    assert seller["domains"] == ["http:/www.coupang.com", "http://www.coupangeats.com"]
    assert seller["email"] == "help@coupang.com"
    assert result["total_count"] == 1


@pytest.mark.parametrize("marker", ["N/A", "NULL", "null", "None", " ", "-"])
async def test_every_empty_marker_becomes_none(marker):
    """이 API 는 빈 값을 여러 문자열로 쓴다. 실응답에서 100행 중 29행이 ``"NULL"`` 이었다."""
    from data_go_mcp.ftc_ecommerce.models import OnlineSeller

    seller = OnlineSeller.from_api({"brno": "1208800767", "rprsvEmladr": marker})
    assert seller.email is None


@respx.mock
async def test_na_strings_become_none():
    """이 API 는 빈 값을 ``"N/A"`` 로 보낸다. 그대로 두면 모델이 가짜 값을 갖는다."""
    respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json=SELLER_RESPONSE))
    async with FtcEcommerceAPIClient() as client:
        result = await client.get_online_seller("1208800767")

    seller = result["items"][0]
    assert seller["fax"] is None
    assert seller["closed_on"] is None
    assert seller["suspended_from"] is None


@respx.mock
async def test_closed_seller_keeps_its_status():
    respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json=CLOSED_RESPONSE))
    async with FtcEcommerceAPIClient() as client:
        result = await client.get_online_seller("514-10-82572")

    seller = result["items"][0]
    assert seller["operating_status"] == "직권말소"
    assert seller["business_status"] == "폐업자"
    assert seller["active"] is False
    assert seller["corporate_number"] is None  # "N/A"
    assert seller["email"] is None  # "NULL" — 이 API 의 두 번째 빈 값 표기


@respx.mock
async def test_active_flag_follows_the_status():
    respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json=SELLER_RESPONSE))
    async with FtcEcommerceAPIClient() as client:
        result = await client.get_online_seller("1208800767")
    assert result["items"][0]["active"] is True


@respx.mock
async def test_unreported_business_is_empty_not_an_error():
    """통신판매 신고를 하지 않은 사업자는 0건이다."""
    respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json=EMPTY_RESPONSE))
    async with FtcEcommerceAPIClient() as client:
        result = await client.get_online_seller("999-99-99999")
    assert result == {"items": [], "total_count": 0}


@respx.mock
async def test_lookup_by_report_number():
    route = respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json=SELLER_RESPONSE))
    async with FtcEcommerceAPIClient() as client:
        await client.get_online_seller(report_number="2026-서울광진-1253")
    params = route.calls.last.request.url.params
    assert params["prmmiMnno"] == "2026-서울광진-1253"
    assert "brno" not in params


async def test_one_of_the_two_keys_is_required():
    """둘 다 없으면 전체 276만 건이 온다 — 보내기 전에 막는다."""
    async with FtcEcommerceAPIClient() as client:
        with pytest.raises(ValueError, match="사업자번호"):
            await client.get_online_seller()


@pytest.mark.parametrize("value", ["120-88-0076", "abc", "12088007670"])
async def test_business_number_must_be_ten_digits(value):
    async with FtcEcommerceAPIClient() as client:
        with pytest.raises(ValueError, match="10자리"):
            await client.get_online_seller(value)


@respx.mock
async def test_api_error_becomes_an_exception():
    respx.get(ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "resultCode": "30",
                "resultMsg": "SERVICE_KEY_IS_NOT_REGISTERED_ERROR",
                "totalCount": 0,
                "items": [],
            },
        )
    )
    async with FtcEcommerceAPIClient() as client:
        with pytest.raises(DataGoAPIError) as excinfo:
            await client.get_online_seller("1208800767")
    assert excinfo.value.result_code == "30"


@respx.mock
async def test_gateway_error_is_raised():
    respx.get(ENDPOINT).mock(
        return_value=httpx.Response(
            403,
            json={
                "OpenAPI_ServiceResponse": {
                    "cmmMsgHeader": {
                        "errMsg": "SERVICE_KEY_IS_NOT_REGISTERED_ERROR",
                        "returnReasonCode": "30",
                    }
                }
            },
        )
    )
    async with FtcEcommerceAPIClient() as client:
        with pytest.raises(DataGoAPIError):
            await client.get_online_seller("1208800767")


async def test_missing_key_is_reported(monkeypatch, tmp_path):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("FTC_ECOMMERCE_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)  # .env 를 읽지 않도록
    with pytest.raises(ValueError, match="API_KEY"):
        FtcEcommerceAPIClient()
