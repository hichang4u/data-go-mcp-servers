"""nps 테스트 공용 fixture — S0b 에서 받은 실제 응답 형태."""

import pytest


BASE = "https://apis.data.go.kr/B552015/NpsBplcInfoInqireServiceV2"

SEARCH_RESPONSE = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL_CODE"},
        "body": {
            "items": {
                "item": [
                    {
                        "bzowrRgstNo": "142816****",
                        "dataCrtYm": "202607",
                        "ldongAddrMgplDgCd": "41",
                        "ldongAddrMgplSgguCd": "220",
                        "ldongAddrMgplSgguEmdCd": "128",
                        "seq": 7101020,
                        "wkplJnngStcd": "1",
                        "wkplNm": "주식회사 유일이엔지",
                        "wkplRoadNmDtlAddr": "경기도 평택시 삼성로",
                        "wkplStylDvcd": "1",
                    }
                ]
            },
            "pageNo": 1,
            "numOfRows": 1,
            "totalCount": 2107,
        },
    }
}

DETAIL_RESPONSE = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL_CODE"},
        "body": {
            "items": {
                "item": [
                    {
                        "adptDt": "20260601",
                        "bzowrRgstNo": "142816****",
                        "crrmmNtcAmt": "7979660",
                        "jnngpCnt": 36,
                        "scsnDt": "00010101",
                        "vldtVlKrnNm": "배관 및 냉ㆍ난방 공사업",
                        "wkplIntpCd": "452104",
                        "wkplNm": "주식회사 유일이엔지",
                    }
                ]
            },
            "pageNo": 1,
            "numOfRows": 1,
            "totalCount": 1,
        },
    }
}

PERIOD_RESPONSE = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "NORMAL_CODE"},
        "body": {
            "items": {"item": [{"lssJnngpCnt": 7, "nwAcqzrCnt": 36}]},
            "pageNo": 1,
            "numOfRows": 1,
            "totalCount": 1,
        },
    }
}


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture
def search_response() -> dict:
    return SEARCH_RESPONSE


@pytest.fixture
def detail_response() -> dict:
    return DETAIL_RESPONSE


@pytest.fixture
def period_response() -> dict:
    return PERIOD_RESPONSE


# 행정안전부_행정표준코드_법정동코드 (StanReginCd) — 2026-09-12 실응답에서 발췌
REGION_BASE = "https://apis.data.go.kr/1741000/StanReginCd"

REGION_RESPONSE = {
    "StanReginCd": [
        {
            "head": [
                {"totalCount": 15},
                {"numOfRows": "3", "pageNo": "1", "type": "JSON"},
                {"RESULT": {"resultCode": "INFO-0", "resultMsg": "NOMAL SERVICE"}},
            ]
        },
        {
            "row": [
                {
                    "region_cd": "1168010100",
                    "sido_cd": "11",
                    "sgg_cd": "680",
                    "umd_cd": "101",
                    "ri_cd": "00",
                    "locatjumin_cd": "1168010100",
                    "locatjijuk_cd": "1168010100",
                    "locatadd_nm": "서울특별시 강남구 역삼동",
                    "locat_order": 1,
                    "locat_rm": "",
                    "locathigh_cd": "1168000000",
                    "locallow_nm": "역삼동",
                    "adpt_de": "",
                },
                {
                    "region_cd": "1168000000",
                    "sido_cd": "11",
                    "sgg_cd": "680",
                    "umd_cd": "000",
                    "ri_cd": "00",
                    "locatjumin_cd": "1168000000",
                    "locatjijuk_cd": "1168000000",
                    "locatadd_nm": "서울특별시 강남구",
                    "locat_order": 2,
                    "locat_rm": "",
                    "locathigh_cd": "1100000000",
                    "locallow_nm": "강남구",
                    "adpt_de": "",
                },
                {
                    "region_cd": "4182025021",
                    "sido_cd": "41",
                    "sgg_cd": "820",
                    "umd_cd": "250",
                    "ri_cd": "21",
                    "locatjumin_cd": "4182025021",
                    "locatjijuk_cd": "4182025021",
                    "locatadd_nm": "경기도 가평군 가평읍 읍내리",
                    "locat_order": 1,
                    "locat_rm": "",
                    "locathigh_cd": "4182025000",
                    "locallow_nm": "읍내리",
                    "adpt_de": "",
                },
            ]
        },
    ]
}

REGION_NO_DATA_RESPONSE = {"RESULT": {"resultCode": "INFO-3", "resultMsg": "데이터없음 에러"}}


@pytest.fixture
def region_base_url() -> str:
    return REGION_BASE


@pytest.fixture
def region_response() -> dict:
    return REGION_RESPONSE


@pytest.fixture
def region_no_data_response() -> dict:
    return REGION_NO_DATA_RESPONSE


# 근로복지공단_고용/산재보험 현황정보 (gySjbPstateInfoService, XML) — 2026-09-13 실응답
INSURANCE_BASE = "https://apis.data.go.kr/B490001/gySjbPstateInfoService"

INSURANCE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header><body><items><item><addr>경기 고양시 덕양구 행주로 58-19 (행주내동) 197-2, 198-3, 197-4</addr><opaBoheomFg>1</opaBoheomFg><post>10439</post><saeopFg>7</saeopFg><saeopjaDrno>1208800767</saeopjaDrno><saeopjangNm>주식회사포워드벤처스/캐슬캠프</saeopjangNm><sangsiInwonCnt>0</sangsiInwonCnt><seongripDt>20140502</seongripDt><sjEopjongCd>50109</sjEopjongCd><sjEopjongNm>소형화물운수업</sjEopjongNm></item><item><addr>서울특별시 광진구 아차산로 412 2층</addr><gyEopjongCd>47919</gyEopjongCd><gyEopjongNm>기타 통신 판매업</gyEopjongNm><opaBoheomFg>2</opaBoheomFg><post>05050</post><saeopFg>1</saeopFg><saeopjaDrno>1208800767</saeopjaDrno><saeopjangNm>쿠팡주식회사</saeopjangNm><sangsiInwonCnt>11070</sangsiInwonCnt><seongripDt>20131001</seongripDt></item><item><addr>서울특별시 광진구 아차산로 412 2층</addr><opaBoheomFg>1</opaBoheomFg><post>05050</post><saeopFg>3</saeopFg><saeopjaDrno>1208800767</saeopjaDrno><saeopjangNm>쿠팡주식회사</saeopjangNm><sangsiInwonCnt>12081</sangsiInwonCnt><seongripDt>20131001</seongripDt><sjEopjongCd>91001</sjEopjongCd><sjEopjongNm>도.소매 및 소비자용품수리업                </sjEopjongNm></item></items><numOfRows>5</numOfRows><pageNo>1</pageNo><totalCount>3</totalCount></body></response>"""

# 한 건이면 xmltodict 가 item 을 리스트가 아니라 dict 로 준다
INSURANCE_SINGLE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header><body><items><item><addr>경기 수원시 영통구 삼성로 129 (매탄동)</addr><gyEopjongCd>26519</gyEopjongCd><gyEopjongNm>비디오 및 기타 영상기기 제조업</gyEopjongNm><opaBoheomFg>2</opaBoheomFg><post>16677</post><saeopFg>1</saeopFg><saeopjaDrno>1248100998</saeopjaDrno><saeopjangNm>삼성전자(주)</saeopjangNm><sangsiInwonCnt>128093</sangsiInwonCnt><seongripDt>19950701</seongripDt></item></items><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>2</totalCount></body></response>"""

INSURANCE_EMPTY_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><response><header><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header><body><items/><numOfRows>5</numOfRows><pageNo>1</pageNo><totalCount>0</totalCount></body></response>"""


@pytest.fixture
def insurance_base_url() -> str:
    return INSURANCE_BASE


@pytest.fixture
def insurance_xml() -> str:
    return INSURANCE_XML


@pytest.fixture
def insurance_single_xml() -> str:
    return INSURANCE_SINGLE_XML


@pytest.fixture
def insurance_empty_xml() -> str:
    return INSURANCE_EMPTY_XML
