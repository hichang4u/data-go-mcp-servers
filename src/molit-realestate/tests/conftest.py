"""molit 테스트 공용 fixture — 2026-09-30 강남구(11680) 2026-08 실제 XML 응답."""

import pytest


BASE = "https://apis.data.go.kr/1613000"

APT_TRADE_XML = """<?xml version="1.0" encoding="utf-8" standalone="yes"?><response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header><body><items><item><aptDong> </aptDong><aptNm>한양2</aptNm><aptSeq>11680-379</aptSeq><bonbun>0493</bonbun><bubun>0000</bubun><buildYear>1978</buildYear><buyerGbn>개인</buyerGbn><cdealDay> </cdealDay><cdealType> </cdealType><dealAmount>790,000</dealAmount><dealDay>29</dealDay><dealMonth>8</dealMonth><dealYear>2026</dealYear><dealingGbn>중개거래</dealingGbn><estateAgentSggNm>서울 강남구</estateAgentSggNm><excluUseAr>147.41</excluUseAr><floor>2</floor><jibun>493</jibun><landCd>1</landCd><landLeaseholdGbn>N</landLeaseholdGbn><rgstDate> </rgstDate><roadNm>압구정로</roadNm><sggCd>11680</sggCd><slerGbn>개인</slerGbn><umdCd>10500</umdCd><umdNm>압구정동</umdNm></item><item><aptDong>101</aptDong><aptNm>대치푸르지오써밋</aptNm><aptSeq>11680-2201</aptSeq><bonbun>0316</bonbun><bubun>0000</bubun><buildYear>2023</buildYear><buyerGbn>개인</buyerGbn><cdealDay>26.09.02</cdealDay><cdealType>O</cdealType><dealAmount>350,000</dealAmount><dealDay>1</dealDay><dealMonth>8</dealMonth><dealYear>2026</dealYear><dealingGbn>직거래</dealingGbn><estateAgentSggNm> </estateAgentSggNm><excluUseAr>59.98</excluUseAr><floor>15</floor><jibun>316</jibun><landCd>1</landCd><landLeaseholdGbn>N</landLeaseholdGbn><rgstDate>26.08.20</rgstDate><roadNm>도곡로</roadNm><sggCd>11680</sggCd><slerGbn>법인</slerGbn><umdCd>10600</umdCd><umdNm>대치동</umdNm></item></items><numOfRows>2</numOfRows><pageNo>1</pageNo><totalCount>95</totalCount></body></response>"""

APT_RENT_XML = """<?xml version="1.0" encoding="utf-8" standalone="yes"?><response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header><body><items><item><aptNm>상록수</aptNm><aptSeq>11680-303</aptSeq><buildYear>1993</buildYear><contractTerm> </contractTerm><contractType> </contractType><dealDay>13</dealDay><dealMonth>8</dealMonth><dealYear>2026</dealYear><deposit>40,000</deposit><excluUseAr>74.54</excluUseAr><floor>3</floor><jibun>734</jibun><monthlyRent>160</monthlyRent><preDeposit> </preDeposit><preMonthlyRent> </preMonthlyRent><roadnm>언주로10길 15</roadnm><sggCd>11680</sggCd><umdNm>역삼동</umdNm><useRRRight> </useRRRight></item><item><aptNm>개포자이프레지던스</aptNm><aptSeq>11680-2301</aptSeq><buildYear>2023</buildYear><contractTerm>26.09~28.09</contractTerm><contractType>신규</contractType><dealDay>20</dealDay><dealMonth>8</dealMonth><dealYear>2026</dealYear><deposit>150,000</deposit><excluUseAr>84.94</excluUseAr><floor>10</floor><jibun>1282</jibun><monthlyRent>0</monthlyRent><preDeposit>120,000</preDeposit><preMonthlyRent>0</preMonthlyRent><roadnm>선릉로</roadnm><sggCd>11680</sggCd><umdNm>개포동</umdNm><useRRRight>사용</useRRRight></item></items><numOfRows>2</numOfRows><pageNo>1</pageNo><totalCount>1121</totalCount></body></response>"""

LAND_TRADE_XML = """<?xml version="1.0" encoding="utf-8" standalone="yes"?><response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header><body><items><item><cdealDay> </cdealDay><cdealType> </cdealType><dealAmount>2,000</dealAmount><dealArea>3.31</dealArea><dealDay>28</dealDay><dealMonth>8</dealMonth><dealYear>2026</dealYear><dealingGbn>직거래</dealingGbn><estateAgentSggNm> </estateAgentSggNm><jibun>6**</jibun><jimok>도로</jimok><landUse>제2종일반주거지역</landUse><sggCd>11680</sggCd><sggNm>강남구</sggNm><shareDealingType>지분</shareDealingType><umdNm>논현동</umdNm></item></items><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>92</totalCount></body></response>"""

SH_TRADE_XML = """<?xml version="1.0" encoding="utf-8" standalone="yes"?><response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header><body><items><item><buildYear>1998</buildYear><buyerGbn>법인</buyerGbn><cdealDay> </cdealDay><cdealType> </cdealType><dealAmount>359,000</dealAmount><dealDay>14</dealDay><dealMonth>8</dealMonth><dealYear>2026</dealYear><dealingGbn>중개거래</dealingGbn><estateAgentSggNm>서울 강남구</estateAgentSggNm><houseType>다가구</houseType><jibun>1***</jibun><plottageAr>179.3</plottageAr><sggCd>11680</sggCd><slerGbn>개인</slerGbn><totalFloorAr>331.2</totalFloorAr><umdNm>논현동</umdNm></item></items><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>4</totalCount></body></response>"""

INDU_TRADE_XML = """<?xml version="1.0" encoding="utf-8" standalone="yes"?><response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header><body><items><item><buildYear>2017</buildYear><buildingAr>62.78</buildingAr><buildingType>집합</buildingType><buildingUse>공장</buildingUse><buyerGbn>법인</buyerGbn><cdealDay> </cdealDay><cdealType> </cdealType><dealAmount>63,500</dealAmount><dealDay>14</dealDay><dealMonth>8</dealMonth><dealYear>2026</dealYear><dealingGbn>중개거래</dealingGbn><estateAgentSggNm>서울 강남구</estateAgentSggNm><floor>2</floor><jibun>649</jibun><landUse>준주거</landUse><plottageAr> </plottageAr><sggCd>11680</sggCd><sggNm>강남구</sggNm><shareDealingType> </shareDealingType><slerGbn>법인</slerGbn><umdNm>자곡동</umdNm></item></items><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>2</totalCount></body></response>"""

EMPTY_XML = """<?xml version="1.0" encoding="utf-8" standalone="yes"?><response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header><body><items/><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>0</totalCount></body></response>"""

ERROR_XML = """<?xml version="1.0" encoding="utf-8" standalone="yes"?><response><header><resultCode>30</resultCode><resultMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</resultMsg></header><body></body></response>"""


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture
def apt_trade_xml() -> str:
    return APT_TRADE_XML


@pytest.fixture
def apt_rent_xml() -> str:
    return APT_RENT_XML


@pytest.fixture
def land_trade_xml() -> str:
    return LAND_TRADE_XML


@pytest.fixture
def sh_trade_xml() -> str:
    return SH_TRADE_XML


@pytest.fixture
def indu_trade_xml() -> str:
    return INDU_TRADE_XML


@pytest.fixture
def empty_xml() -> str:
    return EMPTY_XML


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("MOLIT_REALESTATE_API_KEY", raising=False)
