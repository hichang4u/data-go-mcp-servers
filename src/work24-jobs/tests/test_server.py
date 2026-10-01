"""work24 MCP 툴 테스트."""

import json

import httpx
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.work24_jobs.server import mcp


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


def _xml(body: str) -> httpx.Response:
    return httpx.Response(200, text=body, headers={"content-type": "application/xml"})


async def test_all_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == {"search_job_postings", "get_job_posting"}
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_search_job_postings_by_business_number(base_url, list_xml):
    route = respx.get(url__startswith=base_url).mock(return_value=_xml(list_xml))
    async with Client(mcp) as client:
        result = await client.call_tool("search_job_postings", {"business_number": "503-81-69211"})

    assert route.calls.last.request.url.params["busino"] == "5038169211"
    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["total_count"] == 2
    assert data["items"][0]["company"] == "워터매니지먼트주식회사"
    assert data["items"][0]["min_salary"] == 41000000


@respx.mock
async def test_get_job_posting_returns_company_and_posting(base_url, detail_xml):
    respx.get(url__startswith=base_url).mock(return_value=_xml(detail_xml))
    async with Client(mcp) as client:
        result = await client.call_tool("get_job_posting", {"wanted_auth_no": "K140022610010052"})

    data = json.loads(_text(result))
    assert data["company"]["employee_count"] == "25 명"
    assert data["posting"]["hiring_count"] == "1"


@respx.mock
async def test_empty_result_is_not_an_error(base_url, empty_xml):
    respx.get(url__startswith=base_url).mock(return_value=_xml(empty_xml))
    async with Client(mcp) as client:
        result = await client.call_tool("search_job_postings", {"business_number": "0000000000"})

    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["items"] == [] and data["total_count"] == 0


async def test_no_filter_is_input_error():
    async with Client(mcp) as client:
        result = await client.call_tool("search_job_postings", {})
    assert result.is_error is True
    assert "입력값 오류" in _text(result)


async def test_bad_region_code_is_input_error():
    async with Client(mcp) as client:
        result = await client.call_tool("search_job_postings", {"region_code": "서울"})
    assert result.is_error is True
    assert "지역코드" in _text(result)
