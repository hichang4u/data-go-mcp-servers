"""pps 테스트 공용 fixture — 나라장터 개방표준 응답 형태 (items 가 dict 가 아니라 list)."""

import pytest


BASE = "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService"

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
