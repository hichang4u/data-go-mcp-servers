"""pps 테스트 공용 fixture — 나라장터 개방표준 응답 형태 (items 가 dict 가 아니라 list)."""

import pytest


BASE = "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService"
# 낙찰업체 조회는 개방표준이 아니라 낙찰정보서비스를 쓴다 (업체 정보가 여기에만 있다)
SCSBID_BASE = "https://apis.data.go.kr/1230000/as/ScsbidInfoService"

BID_ITEM = {
    "bidNtceNo": "R26BK01722116",
    "bidNtceOrd": "000",
    "ppsNtceYn": "Y",
    "bidNtceNm": "2026년 도로 유지보수 공사",
    "bidNtceSttusNm": "공고중",
    "bidNtceDate": "2026-09-10",
    "bidNtceBgn": "09:00",
    "bsnsDivNm": "공사",
    "elctrnBidYn": "Y",
    "ntceInsttNm": "서울특별시",
    "dmndInsttNm": "서울특별시",
    "opengDate": "2026-09-20",
    "opengTm": "10:00",
    "presmptPrce": "150000000",
}


def ok(items: list, total: int | None = None, page_no: int = 1, num_of_rows: int = 10) -> dict:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "정상"},
            "body": {
                "items": items,
                "numOfRows": num_of_rows,
                "pageNo": page_no,
                "totalCount": len(items) if total is None else total,
            },
        }
    }


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture
def bid_item() -> dict:
    return dict(BID_ITEM)


@pytest.fixture
def ok_response():
    return ok


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("PPS_NARAJANGTEO_API_KEY", raising=False)


# ── 조달업체 정보 (UsrInfoService02, 2026-10-03 실제 응답) ───────────────────

CORP_BASE = "https://apis.data.go.kr/1230000/ao/UsrInfoService02"

CORP_BASIC = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "정상"},
        "body": {
            "items": [
                {
                    "bizno": "1118126895",
                    "corpNm": "주식회사 레드캡투어",
                    "engCorpNm": "redcaptour",
                    "opbizDt": "1996-08-01 00:00:00",
                    "rgnCd": "11140",
                    "rgnNm": "서울특별시 중구",
                    "zip": "04551",
                    "adrs": "서울특별시 중구 을지로",
                    "dtlAdrs": "100, 비동 19층(을지로2가, 파인에비뉴)",
                    "telNo": "042-714-2392",
                    "faxNo": "070-5088-3267",
                    "cntryNm": "대한민국",
                    "hmpgAdrs": "",
                    "mnfctDivCd": "제240002",
                    "mnfctDivNm": "공급",
                    "emplyeNum": "499",
                    "corpBsnsDivCd": "01,03,05",
                    "corpBsnsDivNm": "물품,일반용역,용역",
                    "hdoffceDivNm": "본사",
                    "rgstDt": "1999-11-10 00:00:00",
                    "chgDt": "2026-09-30 14:34:49",
                    "esntlNoCertRgstYn": "N",
                    "ceoNm": "인유성",
                }
            ],
            "numOfRows": 3,
            "pageNo": 1,
            "totalCount": 1,
        },
    }
}

CORP_INDUSTRY = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "정상"},
        "body": {
            "items": [
                {
                    "bizno": "1118126895",
                    "indstrytyNm": "종합여행업",
                    "indstrytyCd": "1261",
                    "rgstDt": "2007-01-22 00:00:00",
                    "vldPrdExprtDt": "",
                    "systmRgstDt": "2008-09-16 13:50:36",
                    "chgDt": "",
                    "indstrytyStatsNm": "",
                    "rprsntIndstrytyYn": "N",
                    "systmChgDt": "2009-07-17 13:30:30",
                },
                {
                    "bizno": "1118126895",
                    "indstrytyNm": "여객자동차운수사업(자동차대여사업)",
                    "indstrytyCd": "1457",
                    "rgstDt": "1997-11-01 00:00:00",
                    "vldPrdExprtDt": "",
                    "systmRgstDt": "2008-05-06 18:18:11",
                    "chgDt": "",
                    "indstrytyStatsNm": "",
                    "rprsntIndstrytyYn": "Y",
                    "systmChgDt": "2019-04-11 16:14:27",
                },
            ],
            "numOfRows": 3,
            "pageNo": 1,
            "totalCount": 3,
        },
    }
}

CORP_SUPPLY = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "정상"},
        "body": {
            "items": [
                {
                    "bizno": "1118126895",
                    "dtilPrdctClsfcNoNm": "자동차렌트서비스",
                    "dtilPrdctClsfcNo": "7811180801",
                    "rgstDt": "2019-09-23 09:42:41",
                    "chgDt": "2019-09-23 09:42:41",
                    "rprsntPrdctClsfcNoNmYn": "Y",
                    "mnfctYn": "N",
                },
                {
                    "bizno": "1118126895",
                    "dtilPrdctClsfcNoNm": "맞춤형국외공무여행서비스",
                    "dtilPrdctClsfcNo": "9012159801",
                    "rgstDt": "2021-11-22 10:16:55",
                    "chgDt": "2021-11-22 10:16:55",
                    "rprsntPrdctClsfcNoNmYn": "N",
                    "mnfctYn": "N",
                },
            ],
            "numOfRows": 3,
            "pageNo": 1,
            "totalCount": 2,
        },
    }
}

CORP_SANCTION = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "정상"},
        "body": {
            "items": [
                {
                    "unptRsttDocNm": "계약제도발전과-1137(2026.2.19.) 부정당업자 입찰 참가자격 제한 처분 통보[㈜세연인터내셔널]",
                    "bizno": "3278100184",
                    "corpNm": "주식회사 세연인터내셔널",
                    "rsttBgnDate": "2026-02-26",
                    "rsttEndDate": "2026-11-25",
                    "insttCd": "1690000",
                    "insttNm": "방위사업청",
                    "lawordNm": "국가계약법-부정당제재근거법령",
                    "lawordArtclClause": "법27조제1항9호 나목 영76조제2항2호가목",
                    "lawordArtclClauseCd": "001-076-002-002-가-20210706",
                    "lawordArtclClauseCdNm": "정당한 이유 없이 계약을 체결 또는 이행(제42조제5항에 따른 계약이행능력심사를 위하여 제출한 하도급관리계획, 외주근로자 근로조건 이행계획에 관한 사항의 이행과 제72조 및 제72조의2에 따른 공동계약에 관한 사항의 이행을 포함한다)하지 아니하거나 입찰공고와 계약서에 명시된 계약의 주요조건(입찰공고와 계약서에 이행을 하지 아니하였을 경우 입찰참가자격 제한을 받을 수 있음을 명시한 경우에 한정한다)을 위반한 자",
                    "enfcAtcsCd": "[별표 2]2.13가",
                    "enfcPrvNm": "계약을 체결 또는 이행(하자보수의무의 이행을 포함한다)하지 않은 자",
                    "ntfcnDt": "2026-02-20 13:41",
                    "rsttPrdMonthNum": "9",
                    "rsttPrdDayNum": "0",
                    "rsttProgrsNm": "제재",
                }
            ],
            "numOfRows": 3,
            "pageNo": 1,
            "totalCount": 1,
        },
    }
}

CORP_EMPTY = {
    "response": {
        "header": {"resultCode": "00", "resultMsg": "정상"},
        "body": {"items": [], "numOfRows": 3, "pageNo": 1, "totalCount": 0},
    }
}
