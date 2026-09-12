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
