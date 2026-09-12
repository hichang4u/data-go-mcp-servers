"""MsdsChemicalInfoAPIClient 테스트 (KOSHA XML 전용 API)."""

import httpx
import pytest
import respx

from data_go_mcp.core.errors import DataGoAPIError
from data_go_mcp.msds_chemical_info.api_client import MsdsChemicalInfoAPIClient, detect_search_type
from data_go_mcp.msds_chemical_info.models import SearchType


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY")
    with pytest.raises(ValueError, match="API_KEY"):
        MsdsChemicalInfoAPIClient()


@pytest.mark.parametrize(
    "term, expected",
    [
        ("벤젠", SearchType.KOREAN_NAME),
        ("71-43-2", SearchType.CAS_NO),
        ("7440-23-5", SearchType.CAS_NO),
        ("UN1114", SearchType.UN_NO),
        ("1114", SearchType.UN_NO),
        ("KE-02150", SearchType.KE_NO),
        ("200-753-7", SearchType.EN_NO),
    ],
)
def test_detect_search_type(term, expected):
    assert detect_search_type(term) == expected


@respx.mock
async def test_search_chemicals_sends_params_and_parses_xml(base_url, list_xml):
    route = respx.get(f"{base_url}/chemlist").mock(return_value=httpx.Response(200, text=list_xml))
    async with MsdsChemicalInfoAPIClient() as client:
        resp = await client.search_chemicals(
            "벤젠", SearchType.KOREAN_NAME, page_no=1, num_of_rows=10
        )

    q = route.calls.last.request.url.params
    assert q["serviceKey"] == "test-key"
    assert q["searchWrd"] == "벤젠"
    assert q["searchCnd"] == "0"
    assert q["numOfRows"] == "10"

    assert resp.total_count == 3
    item = resp.items[0]
    assert item.chem_id == "001016"
    assert item.chem_name_kor == "벤젠"
    assert item.cas_no == "71-43-2"
    assert item.un_no == "1114"
    assert item.kosha_confirm is None


@respx.mock
async def test_search_with_no_results(base_url, empty_list_xml):
    respx.get(f"{base_url}/chemlist").mock(return_value=httpx.Response(200, text=empty_list_xml))
    async with MsdsChemicalInfoAPIClient() as client:
        resp = await client.search_chemicals("없는물질")
    assert resp.items == []
    assert resp.total_count == 0


@respx.mock
async def test_get_chemical_detail_parses_section_items(base_url, detail_xml):
    route = respx.get(f"{base_url}/chemdetail01").mock(
        return_value=httpx.Response(200, text=detail_xml)
    )
    async with MsdsChemicalInfoAPIClient() as client:
        section = await client.get_chemical_detail("001016", 1)

    assert route.calls.last.request.url.params["chemId"] == "001016"
    assert section.section_number == 1
    assert section.section_title == "화학제품과 회사에 관한 정보"
    assert [i.msds_item_code for i in section.items] == ["A02", "A04", "A0401"]
    assert section.items[0].item_detail == "에탄올아민"
    assert section.items[1].item_detail is None
    assert section.items[2].lev == 2
    assert section.items[2].ordr_idx == 1006


@respx.mock
async def test_detail_endpoint_is_zero_padded(base_url, detail_xml):
    route = respx.get(f"{base_url}/chemdetail16").mock(
        return_value=httpx.Response(200, text=detail_xml)
    )
    async with MsdsChemicalInfoAPIClient() as client:
        await client.get_chemical_detail("001016", 16)
    assert route.called


async def test_invalid_section_number_is_value_error():
    async with MsdsChemicalInfoAPIClient() as client:
        with pytest.raises(ValueError, match="1 and 16"):
            await client.get_chemical_detail("001016", 17)


@respx.mock
async def test_get_sections_fetches_range_concurrently(base_url, detail_xml):
    routes = [
        respx.get(f"{base_url}/chemdetail{n:02d}").mock(
            return_value=httpx.Response(200, text=detail_xml)
        )
        for n in range(1, 5)
    ]
    async with MsdsChemicalInfoAPIClient() as client:
        sections = await client.get_sections("001016", range(1, 5))

    assert all(r.called for r in routes)
    assert list(sections) == [1, 2, 3, 4]
    assert sections[4].section_title == "응급조치요령"


@respx.mock
async def test_get_sections_tolerates_a_failed_section(base_url, detail_xml, error_xml):
    respx.get(f"{base_url}/chemdetail01").mock(return_value=httpx.Response(200, text=detail_xml))
    respx.get(f"{base_url}/chemdetail02").mock(return_value=httpx.Response(200, text=error_xml))
    async with MsdsChemicalInfoAPIClient() as client:
        sections = await client.get_sections("001016", range(1, 3), tolerate_errors=True)

    assert len(sections[1].items) == 3
    assert sections[2].items == []
    assert sections[2].error is not None and "[30]" in sections[2].error


@respx.mock
async def test_error_code_raises_data_go_error(base_url, error_xml):
    respx.get(f"{base_url}/chemlist").mock(return_value=httpx.Response(200, text=error_xml))
    async with MsdsChemicalInfoAPIClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.search_chemicals("벤젠")
    assert exc.value.result_code == "30"


@respx.mock
async def test_empty_xml_elements_do_not_break_parsing(base_url):
    # xmltodict 는 빈 요소를 None 으로 준다 — 필수 필드가 비어도 한 행 때문에 툴 전체가 죽으면 안 된다
    xml = """<response><header><resultCode>00</resultCode><resultMsg>OK</resultMsg></header>
<body><items><item><casNo/><chemId>000123</chemId><chemNameKor/><enNo/><keNo/><unNo/><lastDate/></item></items>
<totalCount>1</totalCount><pageNo>1</pageNo><numOfRows>10</numOfRows></body></response>"""
    respx.get(f"{base_url}/chemlist").mock(return_value=httpx.Response(200, text=xml))
    async with MsdsChemicalInfoAPIClient() as client:
        resp = await client.search_chemicals("x")
    assert resp.items[0].chem_id == "000123"
    assert resp.items[0].chem_name_kor == ""

    detail = """<response><header><resultCode>00</resultCode><resultMsg>OK</resultMsg></header>
<body><items><item><itemDetail/><lev/><msdsItemCode>A02</msdsItemCode><msdsItemNameKor/><ordrIdx/><upMsdsItemCode/></item></items></body></response>"""
    respx.get(f"{base_url}/chemdetail01").mock(return_value=httpx.Response(200, text=detail))
    async with MsdsChemicalInfoAPIClient() as client:
        section = await client.get_chemical_detail("000123", 1)
    assert section.items[0].msds_item_code == "A02"
    assert section.items[0].lev == 1
    assert section.items[0].ordr_idx == 0
