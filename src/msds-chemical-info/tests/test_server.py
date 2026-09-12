"""msds MCP 툴 테스트."""

import json
from typing import Iterable

import httpx
import respx
from mcp import Client
from mcp.types import TextContent

from data_go_mcp.msds_chemical_info.server import mcp


TOOLS = {
    "search_chemicals",
    "get_chemical_safety_summary",
    "get_chemical_handling_info",
    "get_chemical_properties",
    "get_chemical_regulatory_info",
    "get_chemical_section",
    "get_complete_msds",
}


def _text(result) -> str:
    (content,) = result.content
    assert isinstance(content, TextContent)
    return content.text


def _mock_sections(base_url: str, xml: str, numbers: Iterable[int] = range(1, 17)):
    return [
        respx.get(f"{base_url}/chemdetail{n:02d}").mock(return_value=httpx.Response(200, text=xml))
        for n in numbers
    ]


async def test_all_tools_are_read_only_with_described_params():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == TOOLS
    for tool in tools:
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


@respx.mock
async def test_search_auto_detects_cas_number(base_url, list_xml):
    route = respx.get(f"{base_url}/chemlist").mock(return_value=httpx.Response(200, text=list_xml))
    async with Client(mcp) as client:
        result = await client.call_tool("search_chemicals", {"search_term": "71-43-2"})

    assert route.calls.last.request.url.params["searchCnd"] == "1"
    data = json.loads(_text(result))
    assert result.is_error is False
    assert data["search_type_used"] == "CAS_NO"
    assert data["total_count"] == 3
    assert data["items"][0] == {
        "chem_id": "001016",
        "chem_name_kor": "벤젠",
        "cas_no": "71-43-2",
        "un_no": "1114",
        "ke_no": "KE-02150",
        "en_no": "200-753-7",
        "last_date": "2024-01-05",
    }


@respx.mock
async def test_search_explicit_type_and_row_cap(base_url, list_xml):
    route = respx.get(f"{base_url}/chemlist").mock(return_value=httpx.Response(200, text=list_xml))
    async with Client(mcp) as client:
        await client.call_tool(
            "search_chemicals",
            {"search_term": "벤젠", "search_type": "korean_name", "num_of_rows": 500},
        )
    q = route.calls.last.request.url.params
    assert q["searchCnd"] == "0"
    assert q["numOfRows"] == "100"


async def test_search_invalid_type_is_tool_error():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_chemicals", {"search_term": "x", "search_type": "NOPE"}
        )
    assert result.is_error is True
    assert "KOREAN_NAME" in _text(result)


@respx.mock
async def test_get_chemical_section_formats_content(base_url, detail_xml):
    _mock_sections(base_url, detail_xml, [1])
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_chemical_section", {"chem_id": "1016", "section_number": 1}
        )

    data = json.loads(_text(result))
    assert data["chem_id"] == "001016"  # zfill
    assert data["title"] == "화학제품과 회사에 관한 정보"
    assert data["content"].splitlines() == [
        "## 1. 화학제품과 회사에 관한 정보",
        "• 제품명: 에탄올아민",
        "• 제품의 권고 용도와 사용상의 제한: 자료없음",
        "  - 제품의 권고 용도: 자료없음",
    ]


async def test_get_chemical_section_rejects_bad_number():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_chemical_section", {"chem_id": "001016", "section_number": 0}
        )
    assert result.is_error is True
    assert "1 and 16" in _text(result)


@respx.mock
async def test_safety_summary_returns_sections_1_to_4(base_url, detail_xml):
    routes = _mock_sections(base_url, detail_xml, range(1, 5))
    async with Client(mcp) as client:
        result = await client.call_tool("get_chemical_safety_summary", {"chem_id": "001016"})

    assert all(r.called for r in routes)
    data = json.loads(_text(result))
    assert set(data) == {"chem_id", "section_1", "section_2", "section_3", "section_4"}
    assert data["section_4"]["title"] == "응급조치요령"
    assert data["section_1"]["content"].startswith("## 1.")


@respx.mock
async def test_grouped_tools_cover_their_ranges(base_url, detail_xml):
    _mock_sections(base_url, detail_xml)
    async with Client(mcp) as client:
        handling = json.loads(
            _text(await client.call_tool("get_chemical_handling_info", {"chem_id": "001016"}))
        )
        props = json.loads(
            _text(await client.call_tool("get_chemical_properties", {"chem_id": "001016"}))
        )
        reg = json.loads(
            _text(await client.call_tool("get_chemical_regulatory_info", {"chem_id": "001016"}))
        )

    assert set(handling) == {"chem_id", "section_5", "section_6", "section_7", "section_8"}
    assert set(props) == {"chem_id", "section_9", "section_10", "section_11", "section_12"}
    assert set(reg) == {"chem_id", "section_13", "section_14", "section_15", "section_16"}


@respx.mock
async def test_complete_msds_tolerates_one_failed_section(base_url, detail_xml, error_xml):
    _mock_sections(base_url, detail_xml, [n for n in range(1, 17) if n != 9])
    respx.get(f"{base_url}/chemdetail09").mock(return_value=httpx.Response(200, text=error_xml))
    async with Client(mcp) as client:
        result = await client.call_tool("get_complete_msds", {"chem_id": "001016"})

    assert result.is_error is False
    data = json.loads(_text(result))
    assert len(data["sections"]) == 16
    assert data["sections"]["section_9"]["error"].startswith("[30]")
    assert "error" not in data["sections"]["section_1"]


@respx.mock
async def test_api_error_is_tool_error(base_url, error_xml):
    respx.get(f"{base_url}/chemlist").mock(return_value=httpx.Response(200, text=error_xml))
    async with Client(mcp) as client:
        result = await client.call_tool("search_chemicals", {"search_term": "벤젠"})
    assert result.is_error is True
    assert "[30]" in _text(result)
