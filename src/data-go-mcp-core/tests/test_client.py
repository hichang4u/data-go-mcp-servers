"""BaseDataGoClient / to_camel / normalize_items 테스트 (HTTP는 respx로 가로챈다)."""

from typing import Any

import httpx
import pytest
import respx

from data_go_mcp.core.client import BaseDataGoClient, normalize_items, to_camel
from data_go_mcp.core.errors import DataGoAPIError


BASE = "https://apis.data.go.kr/TEST/Service"


class DemoClient(BaseDataGoClient):
    base_url = BASE
    key_env_prefix = "DEMO"
    default_params = {"dataType": "json"}


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "common-key")
    monkeypatch.delenv("DEMO_API_KEY", raising=False)


def ok_body(**body: Any) -> dict[str, Any]:
    return {
        "response": {"header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."}, "body": body}
    }


# --- helpers -------------------------------------------------------------


def test_to_camel_converts_snake_case():
    assert to_camel("ldong_addr_mgpl_dg_cd") == "ldongAddrMgplDgCd"
    assert to_camel("page_no") == "pageNo"
    assert to_camel("crno") == "crno"


@pytest.mark.parametrize(
    "body, expected",
    [
        ({"items": {"item": [{"a": 1}, {"a": 2}]}}, [{"a": 1}, {"a": 2}]),
        ({"items": {"item": {"a": 1}}}, [{"a": 1}]),
        ({"items": [{"a": 1}]}, [{"a": 1}]),
        ({"items": ""}, []),
        ({"items": {}}, []),
        ({}, []),
    ],
)
def test_normalize_items_always_returns_list(body, expected):
    assert normalize_items(body) == expected


# --- request building ----------------------------------------------------


@respx.mock
async def test_get_injects_service_key_and_defaults_and_drops_none():
    route = respx.get(f"{BASE}/getThing").mock(return_value=httpx.Response(200, json=ok_body()))

    async with DemoClient() as client:
        await client.get("getThing", {"wkplNm": "삼성", "bzowrRgstNo": None, "pageNo": 1})

    q = route.calls.last.request.url.params
    assert q["serviceKey"] == "common-key"
    assert q["dataType"] == "json"
    assert q["wkplNm"] == "삼성"
    assert q["pageNo"] == "1"
    assert "bzowrRgstNo" not in q


async def test_explicit_api_key_overrides_env():
    async with DemoClient(api_key="explicit") as client:
        assert client.api_key == "explicit"


async def test_prefixed_env_key_is_used(monkeypatch):
    monkeypatch.setenv("DEMO_API_KEY", "demo-key")
    async with DemoClient() as client:
        assert client.api_key == "demo-key"


# --- response handling ---------------------------------------------------


@respx.mock
async def test_get_returns_unwrapped_body_on_success():
    respx.get(f"{BASE}/getThing").mock(
        return_value=httpx.Response(200, json=ok_body(totalCount=1, items={"item": [{"x": 1}]}))
    )
    async with DemoClient() as client:
        body = await client.get("getThing")

    assert body["totalCount"] == 1
    assert normalize_items(body) == [{"x": 1}]


@respx.mock
async def test_get_raises_data_go_error_when_result_code_not_ok():
    respx.get(f"{BASE}/getThing").mock(
        return_value=httpx.Response(
            200,
            json={
                "response": {"header": {"resultCode": "22", "resultMsg": "LIMITED"}, "body": {}}
            },
        )
    )
    async with DemoClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.get("getThing")

    assert exc.value.result_code == "22"
    assert exc.value.result_msg == "LIMITED"


@respx.mock
async def test_get_maps_gateway_auth_error_to_data_go_error():
    # S0b 에서 관측한 실제 형태: 활용신청 전 HTTP 403 + OpenAPI_ServiceResponse
    respx.get(f"{BASE}/getThing").mock(
        return_value=httpx.Response(
            403,
            json={
                "OpenAPI_ServiceResponse": {
                    "cmmMsgHeader": {
                        "errMsg": "SERVICE_KEY_IS_NOT_REGISTERED_ERROR",
                        "returnAuthMsg": "등록되지 않은 서비스키",
                        "returnReasonCode": "30",
                    }
                }
            },
        )
    )
    async with DemoClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.get("getThing")

    assert exc.value.result_code == "30"
    assert "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in exc.value.result_msg


@respx.mock
async def test_get_raises_http_status_error_on_5xx():
    respx.get(f"{BASE}/getThing").mock(return_value=httpx.Response(502, text="bad gateway"))
    async with DemoClient() as client:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get("getThing")


@respx.mock
async def test_post_sends_json_body_with_key_in_query():
    route = respx.post(f"{BASE}/validate").mock(return_value=httpx.Response(200, json=ok_body()))
    async with DemoClient() as client:
        await client.post("validate", json={"b_no": ["1234567890"]})

    req = route.calls.last.request
    assert req.url.params["serviceKey"] == "common-key"
    assert req.headers["content-type"].startswith("application/json")
    assert b'"b_no"' in req.content


# --- subclass hook (odcloud 형태) ------------------------------------------


class OdcloudClient(BaseDataGoClient):
    base_url = "https://api.odcloud.kr/api/demo/v1"
    key_env_prefix = "DEMO"
    default_params = {"returnType": "JSON"}

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        status = data.get("status_code")
        if status not in (None, "OK"):
            raise DataGoAPIError(str(status), str(data.get("msg", "")))
        return data


@respx.mock
async def test_subclass_can_override_response_check():
    respx.post("https://api.odcloud.kr/api/demo/v1/status").mock(
        return_value=httpx.Response(200, json={"status_code": "OK", "data": [{"b_no": "1"}]})
    )
    async with OdcloudClient() as client:
        data = await client.post("status", json={"b_no": ["1"]})

    assert data["data"] == [{"b_no": "1"}]


# --- lifecycle -----------------------------------------------------------


async def test_context_manager_closes_http_client():
    async with DemoClient() as client:
        http = client.http
        assert not http.is_closed
    assert http.is_closed


@respx.mock
async def test_odcloud_auth_error_maps_to_data_go_error():
    # S0b 에서 관측한 odcloud 형태: HTTP 401 + {"code": -401, "msg": ...}
    respx.post("https://api.odcloud.kr/api/demo/v1/status").mock(
        return_value=httpx.Response(
            401, json={"code": -401, "msg": "유효하지 않은 인증키 입니다."}
        )
    )
    async with OdcloudClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.post("status", json={})

    assert exc.value.result_code == "-401"
    assert exc.value.result_msg == "유효하지 않은 인증키 입니다."


GATEWAY_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    "<OpenAPI_ServiceResponse><cmmMsgHeader><errMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</errMsg>"
    "<returnAuthMsg>등록되지 않은 서비스키</returnAuthMsg><returnReasonCode>30</returnReasonCode>"
    "</cmmMsgHeader></OpenAPI_ServiceResponse>"
)


class XmlDemoClient(BaseDataGoClient):
    base_url = BASE
    key_env_prefix = "DEMO"
    response_format = "xml"


@pytest.mark.parametrize("status", [403, 200])
@respx.mock
async def test_xml_gateway_error_maps_to_data_go_error(status):
    # XML 서비스(근로복지공단 등)는 게이트웨이 오류도 XML 로 온다. 200 으로 오는 경우도 같은 형태.
    respx.get(f"{BASE}/getThing").mock(return_value=httpx.Response(status, text=GATEWAY_XML))
    async with XmlDemoClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.get("getThing")

    assert exc.value.result_code == "30"
    assert "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in exc.value.result_msg


def test_shared_key_false_client_ignores_common_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "data-go-key")
    monkeypatch.delenv("OTHER_PORTAL_API_KEY", raising=False)

    class OtherPortalClient(BaseDataGoClient):
        base_url = "https://example.test/api"
        key_env_prefix = "OTHER_PORTAL"
        shared_key = False
        key_url = "https://example.test"

    with pytest.raises(ValueError, match="OTHER_PORTAL_API_KEY"):
        OtherPortalClient()
