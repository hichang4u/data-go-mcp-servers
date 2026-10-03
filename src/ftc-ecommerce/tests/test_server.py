"""통신판매사업자 툴 테스트 — 인프로세스 mcp.Client 호출."""

import json

import httpx
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.ftc_ecommerce.server import mcp

from .conftest import BASE, EMPTY_RESPONSE, SELLER_RESPONSE


ENDPOINT = f"{BASE}/getMllBsInfoDetail_3"


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


async def test_tool_is_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == {"get_online_seller"}
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_get_online_seller_tool():
    respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json=SELLER_RESPONSE))
    async with Client(mcp) as client:
        result = await client.call_tool("get_online_seller", {"business_number": "120-88-00767"})

    assert result.is_error is False
    data = json.loads(_text(result))
    assert data["items"][0]["name"] == "쿠팡주식회사"
    assert data["items"][0]["corporate_number"] == "1101115067718"
    assert data["total_count"] == 1


@respx.mock
async def test_unreported_business_returns_zero():
    respx.get(ENDPOINT).mock(return_value=httpx.Response(200, json=EMPTY_RESPONSE))
    async with Client(mcp) as client:
        result = await client.call_tool("get_online_seller", {"business_number": "999-99-99999"})

    assert result.is_error is False
    assert json.loads(_text(result))["total_count"] == 0


async def test_bad_business_number_is_an_error_result():
    async with Client(mcp) as client:
        result = await client.call_tool("get_online_seller", {"business_number": "123"})
    assert result.is_error is True
    assert "10자리" in _text(result)


@respx.mock
async def test_api_failure_is_an_error_result():
    respx.get(ENDPOINT).mock(
        return_value=httpx.Response(
            200, json={"resultCode": "30", "resultMsg": "NOT REGISTERED", "items": []}
        )
    )
    async with Client(mcp) as client:
        result = await client.call_tool("get_online_seller", {"business_number": "1208800767"})
    assert result.is_error is True
    assert "30" in _text(result)
