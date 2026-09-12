"""parse_xml_response 테스트 — JSON 응답과 같은 dict 형태로 맞춘다."""

import httpx
import pytest
import respx
from data_go_mcp.core.client import BaseDataGoClient, normalize_items
from data_go_mcp.core.errors import DataGoAPIError
from data_go_mcp.core.xml import parse_xml_response


# S0b 에서 KOSHA 가 실제로 돌려준 형태
KOSHA_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header>
<body><items><item><casNo>71-43-2</casNo><chemId>001016</chemId><chemNameKor>벤젠</chemNameKor>
<enNo>200-753-7</enNo><keNo>KE-02150</keNo><koshaConfirm/><lastDate>2024-01-05</lastDate>
<openYn/><unNo>1114</unNo></item></items><numOfRows>1</numOfRows><pageNo>1</pageNo>
<totalCount>3</totalCount></body></response>"""


def test_parses_standard_response_into_json_like_dict():
    data = parse_xml_response(KOSHA_XML)

    assert data["response"]["header"]["resultCode"] == "00"
    body = data["response"]["body"]
    assert body["totalCount"] == "3"
    assert normalize_items(body) == [
        {
            "casNo": "71-43-2",
            "chemId": "001016",
            "chemNameKor": "벤젠",
            "enNo": "200-753-7",
            "keNo": "KE-02150",
            "koshaConfirm": None,
            "lastDate": "2024-01-05",
            "openYn": None,
            "unNo": "1114",
        }
    ]


def test_empty_items_element_normalizes_to_empty_list():
    xml = "<response><header><resultCode>00</resultCode></header><body><items/><totalCount>0</totalCount></body></response>"

    body = parse_xml_response(xml)["response"]["body"]

    assert normalize_items(body) == []


def test_invalid_xml_raises_value_error():
    with pytest.raises(ValueError, match="XML"):
        parse_xml_response("<response><header>")


class XmlClient(BaseDataGoClient):
    base_url = "https://msds.kosha.or.kr/openapi/service/msdschem"
    key_env_prefix = "MSDS"
    response_format = "xml"


@respx.mock
async def test_xml_client_unwraps_body_and_checks_result_code(monkeypatch):
    monkeypatch.setenv("API_KEY", "k")
    respx.get("https://msds.kosha.or.kr/openapi/service/msdschem/chemlist").mock(
        return_value=httpx.Response(200, text=KOSHA_XML)
    )
    async with XmlClient() as client:
        body = await client.get("chemlist", {"searchWrd": "benzene"})

    assert normalize_items(body)[0]["chemNameKor"] == "벤젠"


@respx.mock
async def test_xml_client_raises_on_error_code(monkeypatch):
    monkeypatch.setenv("API_KEY", "k")
    respx.get("https://msds.kosha.or.kr/openapi/service/msdschem/chemlist").mock(
        return_value=httpx.Response(
            200,
            text="<response><header><resultCode>30</resultCode><resultMsg>KEY</resultMsg></header></response>",
        )
    )
    async with XmlClient() as client:
        with pytest.raises(DataGoAPIError) as exc:
            await client.get("chemlist")
    assert exc.value.result_code == "30"
