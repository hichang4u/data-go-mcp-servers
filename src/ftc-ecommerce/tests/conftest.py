"""공정위 통신판매사업자 — 실응답 fixture (2026-10-03).

``"N/A"`` 문자열이 빈 값이다. 응답은 ``response`` 래핑 없이 최상위에 바로 온다.
"""

import pytest


BASE = "https://apis.data.go.kr/1130000/MllBsDtl_3Service"

SELLER_RESPONSE = {
    "resultCode": "00",
    "resultMsg": "NORMAL SERVICE",
    "numOfRows": "1",
    "pageNo": "1",
    "totalCount": 1,
    "items": [
        {
            "opnSn": "873695980969798743",
            "prmmiYr": "2013",
            "prmmiMnno": "2026-서울광진-1253",
            "ctpvNm": "서울특별시",
            "dclrInstNm": "서울특별시 광진구",
            "operSttusCdNm": "정상영업",
            "smtxTrgtYnCn": "비대상",
            "corpYnNm": "법인",
            "bzmnNm": "쿠팡주식회사",
            "bzmnRgsSttusSeNm": "계속사업자",
            "crno": "1101115067718",
            "brno": "1208800767",
            "telno": "15777011",
            "fxno": "N/A",
            "lctnRnAddr": "서울특별시 광진구 아차산로",
            "lctnAddr": "서울특별시 광진구 자양동 870 번지 업무시설(A동)",
            "domnCn": "http:/www.coupang.com  http://www.coupangeats.com",
            "opnServerPlaceAladr": "N/A",
            "ntslMthdNm": "02",
            "ntslMthdCn": "인터넷",
            "trtmntPrdlstNm": "01",
            "ntslPrdlstCn": "종합몰",
            "dclrCn": None,
            "chgCn": "도메인삭제2017.04.12 상호 / 소재지 변경구 : 주식회사 포워드벤처스 / 강남구 테헤란*** ***(삼성동)2020.10.***표자 변경",
            "chgRsnCn": "도메인삭제2017.04.12 상호 / 소재지 변경구 : 주식회사 포워드벤처스 / 강남구 테헤란*** ***(삼성동)2020.10.***표자 변경",
            "tcbizBgngDate": "N/A",
            "tcbizEndDate": "N/A",
            "clsbizDate": "N/A",
            "bsnResmptDate": "N/A",
            "spcssRsnCn": "N/A",
            "dclrDate": "20130821",
            "lctnRnOzip": "05050",
            "rnAddr": "서울특별시 광진구 아차산로",
            "opnMdfcnDt": "20260724000000",
            "prcsDeptDtlNm": "서울특별시 광진구 기획경제국 지역경제과",
            "prcsDeptAreaNm": "서울특별시 광진구",
            "prcsDeptNm": "지역경제과",
            "chrgDeptTelno": "02-450-1114",
            "rprsvNm": "김범석,로저스 해롤드 린(Rogers Harold Lynn)",
            "rprsvEmladr": "help@coupang.com",
        }
    ],
}

CLOSED_RESPONSE = {
    "resultCode": "00",
    "resultMsg": "NORMAL SERVICE",
    "numOfRows": "1",
    "pageNo": "1",
    "totalCount": 1,
    "items": [
        {
            "opnSn": "897655992669798862",
            "prmmiYr": "2002",
            "prmmiMnno": "1137",
            "ctpvNm": "대구광역시",
            "dclrInstNm": "대구광역시 남구",
            "operSttusCdNm": "직권말소",
            "smtxTrgtYnCn": "N/A",
            "corpYnNm": "N/A",
            "bzmnNm": "코리아뱅크",
            "bzmnRgsSttusSeNm": "폐업자",
            "crno": "N/A",
            "brno": "5141082572",
            "telno": "N/A",
            "fxno": "N/A",
            "lctnRnAddr": "대구광역시 남구 봉덕로",
            "lctnAddr": "대구광역시 남구 봉덕동 *** 번지",
            "domnCn": "N/A",
            "opnServerPlaceAladr": "N/A",
            "ntslMthdNm": "N/A",
            "ntslMthdCn": "N/A",
            "trtmntPrdlstNm": "N/A",
            "ntslPrdlstCn": "N/A",
            "dclrCn": "N/A",
            "chgCn": "N/A",
            "chgRsnCn": "N/A",
            "tcbizBgngDate": "N/A",
            "tcbizEndDate": "N/A",
            "clsbizDate": "N/A",
            "bsnResmptDate": "N/A",
            "spcssRsnCn": "N/A",
            "dclrDate": "20020426",
            "lctnRnOzip": "N/A",
            "rnAddr": "N/A",
            "opnMdfcnDt": "N/A",
            "prcsDeptDtlNm": "대구광역시 남구 행정지원국 시장경제과",
            "prcsDeptAreaNm": "대구광역시 남구",
            "prcsDeptNm": "시장경제과",
            "chrgDeptTelno": "053 664 2191",
            "rprsvNm": "김**",
            "rprsvEmladr": "NULL",
        }
    ],
}

EMPTY_RESPONSE = {
    "resultCode": "00",
    "resultMsg": "NORMAL SERVICE",
    "numOfRows": "1",
    "pageNo": "1",
    "totalCount": 0,
    "items": [],
}


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "TEST_KEY")
