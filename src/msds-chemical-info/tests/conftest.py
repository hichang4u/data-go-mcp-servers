"""msds 테스트 공용 fixture — 2026-09-12 KOSHA 실제 XML 응답 형태."""

import pytest


BASE = "https://msds.kosha.or.kr/openapi/service/msdschem"

LIST_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header>
<body><items>
<item><casNo>71-43-2</casNo><chemId>001016</chemId><chemNameKor>벤젠</chemNameKor><enNo>200-753-7</enNo>
<keNo>KE-02150</keNo><koshaConfirm/><lastDate>2024-01-05</lastDate><openYn/><unNo>1114</unNo></item>
</items><numOfRows>10</numOfRows><pageNo>1</pageNo><totalCount>3</totalCount></body></response>"""

EMPTY_LIST_XML = """<response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header>
<body><items/><numOfRows>10</numOfRows><pageNo>1</pageNo><totalCount>0</totalCount></body></response>"""

DETAIL_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header>
<body><items>
<item><itemDetail>에탄올아민</itemDetail><lev>1</lev><msdsItemCode>A02</msdsItemCode><msdsItemNameKor>제품명</msdsItemNameKor><ordrIdx>1002</ordrIdx><upMsdsItemCode>A</upMsdsItemCode></item>
<item><lev>1</lev><msdsItemCode>A04</msdsItemCode><msdsItemNameKor>제품의 권고 용도와 사용상의 제한</msdsItemNameKor><ordrIdx>1004</ordrIdx><upMsdsItemCode>A</upMsdsItemCode></item>
<item><itemDetail>자료없음</itemDetail><lev>2</lev><msdsItemCode>A0401</msdsItemCode><msdsItemNameKor>제품의 권고 용도</msdsItemNameKor><ordrIdx>1006</ordrIdx><upMsdsItemCode>A04</upMsdsItemCode></item>
</items></body></response>"""

ERROR_XML = """<response><header><resultCode>30</resultCode><resultMsg>SERVICE KEY IS NOT REGISTERED ERROR.</resultMsg></header></response>"""


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture
def list_xml() -> str:
    return LIST_XML


@pytest.fixture
def empty_list_xml() -> str:
    return EMPTY_LIST_XML


@pytest.fixture
def detail_xml() -> str:
    return DETAIL_XML


@pytest.fixture
def error_xml() -> str:
    return ERROR_XML


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("MSDS_CHEMICAL_INFO_API_KEY", raising=False)
