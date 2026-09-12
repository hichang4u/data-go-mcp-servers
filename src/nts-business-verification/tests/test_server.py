"""nts MCP 툴 테스트."""

import json

import httpx
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.nts_business_verification.server import mcp


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


async def test_all_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == {
        "validate_business",
        "check_business_status",
        "batch_validate_businesses",
    }
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_validate_business_normalizes_input_and_returns_result(base_url, validate_match):
    route = respx.post(f"{base_url}/validate").mock(
        return_value=httpx.Response(200, json=validate_match)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "validate_business",
            {
                "business_number": "120-88-00767",
                "start_date": "2000-01-01",
                "representative_name": "홍길동",
            },
        )

    sent = json.loads(route.calls.last.request.content)["businesses"][0]
    assert sent["b_no"] == "1208800767"
    assert sent["start_dt"] == "20000101"

    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["valid"] == "01"
    assert data["valid_msg"] == "일치"
    assert data["status"]["b_stt"] == "계속사업자"


@respx.mock
async def test_validate_business_mismatch_is_a_normal_result(base_url, validate_mismatch):
    respx.post(f"{base_url}/validate").mock(
        return_value=httpx.Response(200, json=validate_mismatch)
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "validate_business",
            {
                "business_number": "1208800767",
                "start_date": "20000101",
                "representative_name": "홍길동",
            },
        )

    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["valid"] == "02"
    assert data["valid_msg"] == "확인할 수 없습니다."
    assert data["status"] is None


async def test_validate_business_rejects_bad_number():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "validate_business",
            {"business_number": "123", "start_date": "20000101", "representative_name": "홍"},
        )
    assert result.is_error is True
    assert "10자리" in _text(result)


@respx.mock
async def test_check_business_status_reshapes_fields(base_url, status_response):
    respx.post(f"{base_url}/status").mock(return_value=httpx.Response(200, json=status_response))
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_business_status", {"business_numbers": "120-88-00767, 0000000000"}
        )

    data = json.loads(_text(result))
    assert data["request_count"] == 2
    assert data["match_count"] == 1
    first, second = data["businesses"]
    assert first == {
        "business_number": "1208800767",
        "status": "계속사업자",
        "status_code": "01",
        "tax_type": "부가가치세 일반과세자",
        "tax_type_code": "01",
        "utcc_yn": "N",
        "rbf_tax_type": "해당없음",
        "rbf_tax_type_code": "99",
    }
    assert second["tax_type"] == "국세청에 등록되지 않은 사업자등록번호입니다."


async def test_check_business_status_rejects_invalid_numbers():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_business_status", {"business_numbers": "123,1208800767"}
        )
    assert result.is_error is True
    assert "123" in _text(result)


@respx.mock
async def test_batch_validate_parses_json_and_cleans_hyphens(base_url, validate_match):
    route = respx.post(f"{base_url}/validate").mock(
        return_value=httpx.Response(200, json=validate_match)
    )
    payload = json.dumps([{"b_no": "120-88-00767", "start_dt": "2000-01-01", "p_nm": "홍길동"}])
    async with Client(mcp) as client:
        result = await client.call_tool("batch_validate_businesses", {"businesses_json": payload})

    sent = json.loads(route.calls.last.request.content)["businesses"][0]
    assert sent["b_no"] == "1208800767"
    assert sent["start_dt"] == "20000101"
    data = json.loads(_text(result))
    assert data["request_count"] == 1
    assert data["valid_count"] == 1
    assert data["results"][0]["valid"] == "01"


async def test_batch_validate_rejects_bad_json():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "batch_validate_businesses", {"businesses_json": "{not json"}
        )
    assert result.is_error is True
    assert "JSON" in _text(result)


async def test_batch_validate_requires_mandatory_fields():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "batch_validate_businesses", {"businesses_json": json.dumps([{"b_no": "1208800767"}])}
        )
    assert result.is_error is True
    assert "start_dt" in _text(result)


@respx.mock
async def test_api_error_is_tool_error(base_url):
    respx.post(f"{base_url}/status").mock(
        return_value=httpx.Response(
            401, json={"code": -401, "msg": "유효하지 않은 인증키 입니다."}
        )
    )
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_business_status", {"business_numbers": "1208800767"}
        )
    assert result.is_error is True
    assert "유효하지 않은 인증키" in _text(result)
