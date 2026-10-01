"""molit 테스트 공용 fixture — 2026-09-30 강남구(11680) 2026-08 실제 XML 응답."""

import pytest


BASE = "https://apis.data.go.kr/1613000"

APT_TRADE_XML = """<?xml version="1.0" encoding="utf-8" standalone="yes"?><response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header><body><items><item><aptDong> </aptDong><aptNm>한양2</aptNm><aptSeq>11680-379</aptSeq><bonbun>0493</bonbun><bubun>0000</bubun><buildYear>1978</buildYear><buyerGbn>개인</buyerGbn><cdealDay> </cdealDay><cdealType> </cdealType><dealAmount>790,000</dealAmount><dealDay>29</dealDay><dealMonth>8</dealMonth><dealYear>2026</dealYear><dealingGbn>중개거래</dealingGbn><estateAgentSggNm>서울 강남구</estateAgentSggNm><excluUseAr>147.41</excluUseAr><floor>2</floor><jibun>493</jibun><landCd>1</landCd><landLeaseholdGbn>N</landLeaseholdGbn><rgstDate> </rgstDate><roadNm>압구정로</roadNm><sggCd>11680</sggCd><slerGbn>개인</slerGbn><umdCd>11000</umdCd><umdNm>압구정동</umdNm></item><item><aptDong>101</aptDong><aptNm>대치푸르지오써밋</aptNm><aptSeq>11680-2201</aptSeq><bonbun>0316</bonbun><bubun>0000</bubun><buildYear>2023</buildYear><buyerGbn>개인</buyerGbn><cdealDay>26.09.02</cdealDay><cdealType>O</cdealType><dealAmount>350,000</dealAmount><dealDay>1</dealDay><dealMonth>8</dealMonth><dealYear>2026</dealYear><dealingGbn>직거래</dealingGbn><estateAgentSggNm> </estateAgentSggNm><excluUseAr>59.98</excluUseAr><floor>15</floor><jibun>316</jibun><landCd>1</landCd><landLeaseholdGbn>N</landLeaseholdGbn><rgstDate>26.08.20</rgstDate><roadNm>도곡로</roadNm><sggCd>11680</sggCd><slerGbn>법인</slerGbn><umdCd>10600</umdCd><umdNm>대치동</umdNm></item></items><numOfRows>2</numOfRows><pageNo>1</pageNo><totalCount>95</totalCount></body></response>"""

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


# ── 건축HUB 건축물대장 (2026-10-01 실제 응답, 삼성동 1-1) ─────────────────────

BLD_BASE = "https://apis.data.go.kr/1613000/BldRgstHubService"

BLD_TITLE_XML = """<response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE</resultMsg></header><body><items><item><rnum>1</rnum><platPlc>서울특별시 강남구 삼성동 1-1번지</platPlc><sigunguCd>11680</sigunguCd><bjdongCd>10500</bjdongCd><platGbCd>0</platGbCd><bun>0001</bun><ji>0001</ji><mgmBldrgstPk>102419120</mgmBldrgstPk><regstrGbCd>1</regstrGbCd><regstrGbCdNm>일반</regstrGbCdNm><regstrKindCd>2</regstrKindCd><regstrKindCdNm>일반건축물</regstrKindCdNm><newPlatPlc>서울특별시 강남구 학동로 402 (삼성동)</newPlatPlc><bldNm> </bldNm><splotNm> </splotNm><block> </block><lot> </lot><bylotCnt>2</bylotCnt><naRoadCd>116803122011</naRoadCd><naBjdongCd>10502</naBjdongCd><naUgrndCd>0</naUgrndCd><naMainBun>402</naMainBun><naSubBun>0</naSubBun><dongNm> </dongNm><mainAtchGbCd>0</mainAtchGbCd><mainAtchGbCdNm>주건축물</mainAtchGbCdNm><platArea>2003.6</platArea><archArea>942.02</archArea><bcRat>47.02</bcRat><totArea>8862.1</totArea><vlRatEstmTotArea>7368.18</vlRatEstmTotArea><vlRat>367.75</vlRat><strctCd>21</strctCd><strctCdNm>철근콘크리트구조</strctCdNm><etcStrct>철근콘크리트조</etcStrct><mainPurpsCd>14000</mainPurpsCd><mainPurpsCdNm>업무시설</mainPurpsCdNm><etcPurps>업무시설 근린생활시설 위락시설</etcPurps><roofCd>10</roofCd><roofCdNm>(철근)콘크리트</roofCdNm><etcRoof>슬라브</etcRoof><hhldCnt>0</hhldCnt><fmlyCnt>0</fmlyCnt><heit>0</heit><grndFlrCnt>8</grndFlrCnt><ugrndFlrCnt>2</ugrndFlrCnt><rideUseElvtCnt>0</rideUseElvtCnt><emgenUseElvtCnt>0</emgenUseElvtCnt><atchBldCnt>0</atchBldCnt><atchBldArea>0</atchBldArea><totDongTotArea>8862.1</totDongTotArea><indrMechUtcnt>0</indrMechUtcnt><indrMechArea>0</indrMechArea><oudrMechUtcnt>0</oudrMechUtcnt><oudrMechArea>0</oudrMechArea><indrAutoUtcnt>33</indrAutoUtcnt><indrAutoArea>1044.94</indrAutoArea><oudrAutoUtcnt>27</oudrAutoUtcnt><oudrAutoArea>0</oudrAutoArea><pmsDay> </pmsDay><stcnsDay> </stcnsDay><useAprDay>19781101</useAprDay><pmsnoYear> </pmsnoYear><pmsnoKikCd> </pmsnoKikCd><pmsnoKikCdNm> </pmsnoKikCdNm><pmsnoGbCd> </pmsnoGbCd><pmsnoGbCdNm> </pmsnoGbCdNm><hoCnt>0</hoCnt><engrGrade> </engrGrade><engrRat>0</engrRat><engrEpi>0</engrEpi><gnBldGrade> </gnBldGrade><gnBldCert>0</gnBldCert><itgBldGrade> </itgBldGrade><itgBldCert>0</itgBldCert><crtnDay>20220813</crtnDay><rserthqkDsgnApplyYn>0</rserthqkDsgnApplyYn><rserthqkAblty> </rserthqkAblty></item></items><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>1</totalCount></body></response>"""

BLD_FLOOR_XML = """<response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE</resultMsg></header><body><items><item><rnum>1</rnum><platPlc>서울특별시 강남구 삼성동 1-1번지</platPlc><sigunguCd>11680</sigunguCd><bjdongCd>10500</bjdongCd><platGbCd>0</platGbCd><bun>0001</bun><ji>0001</ji><mgmBldrgstPk>102419120</mgmBldrgstPk><newPlatPlc>서울특별시 강남구 학동로 402 (삼성동)</newPlatPlc><bldNm> </bldNm><splotNm> </splotNm><block> </block><lot> </lot><naRoadCd>116803122011</naRoadCd><naBjdongCd>10502</naBjdongCd><naUgrndCd>0</naUgrndCd><naMainBun>402</naMainBun><naSubBun>0</naSubBun><dongNm> </dongNm><flrGbCd>10</flrGbCd><flrGbCdNm>지하</flrGbCdNm><flrNo>1</flrNo><flrNoNm>지하1층</flrNoNm><strctCd>21</strctCd><strctCdNm>철근콘크리트구조</strctCdNm><etcStrct>철근콘크리트조</etcStrct><mainPurpsCd>20001</mainPurpsCd><mainPurpsCdNm>주차장</mainPurpsCdNm><etcPurps>주차장,기계실</etcPurps><mainAtchGbCd>0</mainAtchGbCd><mainAtchGbCdNm>주건축물</mainAtchGbCdNm><area>1459.44</area><areaExctYn> </areaExctYn><crtnDay>20220813</crtnDay></item></items><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>20</totalCount></body></response>"""

BLD_EMPTY_XML = """<response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE</resultMsg></header><body><items/><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>0</totalCount></body></response>"""

BLD_TIMEOUT_XML = """<?xml version="1.0" encoding="UTF-8"?><OpenAPI_ServiceResponse><cmmMsgHeader><errMsg>SERVICETIMEOUT_ERROR</errMsg><returnAuthMsg>SERVICETIMEOUT_ERROR</returnAuthMsg><returnReasonCode>26</returnReasonCode></cmmMsgHeader></OpenAPI_ServiceResponse>"""

BLD_HSPRC_XML = """<?xml version="1.0" encoding="UTF-8"?><response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header><body><items><item><rnum>1</rnum><platPlc>서울특별시 강남구 압구정동 493번지</platPlc><sigunguCd>11680</sigunguCd><bjdongCd>11000</bjdongCd><bun>0493</bun><ji>0000</ji><regstrGbCdNm>집합</regstrGbCdNm><regstrKindCdNm>전유부</regstrKindCdNm><bldNm>영동한양아파트 제25동</bldNm><hsprc>3344000000</hsprc><stdDay>20240101</stdDay></item></items><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>5920</totalCount></body></response>"""

BLD_EXPOS_XML = """<?xml version="1.0" encoding="UTF-8"?><response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header><body><items><item><rnum>1</rnum><platPlc>서울특별시 강남구 압구정동 493번지</platPlc><sigunguCd>11680</sigunguCd><bjdongCd>11000</bjdongCd><bun>0493</bun><ji>0000</ji><bldNm>영동한양아파트 제21동</bldNm><dongNm>21</dongNm><hoNm>103호</hoNm><flrGbCdNm>지상</flrGbCdNm><flrNoNm>1층</flrNoNm><exposPubuseGbCdNm>전유</exposPubuseGbCdNm><mainPurpsCdNm>아파트</mainPurpsCdNm><area>147.41</area></item></items><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>1479</totalCount></body></response>"""
