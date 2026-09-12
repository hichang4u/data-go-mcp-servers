"""fsc 테스트 공용 fixture — 2026-09-12 실제 응답(삼성전자 2023)을 줄인 것."""

import pytest

BASE = "https://apis.data.go.kr/1160100/service/GetFinaStatInfoService_V2"


def wrap(items: list, total: int | None = None) -> dict:
    return {
        "response": {
            "body": {
                "items": {"item": items},
                "numOfRows": len(items),
                "pageNo": 1,
                "totalCount": len(items) if total is None else total,
            },
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        }
    }


SUMMARY_ITEM = {
    "basDt": "20231231",
    "crno": "1301110006246",
    "bizYear": "2023",
    "fnclDcd": "110",
    "fnclDcdNm": "연결요약재무제표",
    "enpSaleAmt": "258935494000000",
    "enpBzopPft": "6566976000000",
    "iclsPalClcAmt": "11006265000000",
    "enpCrtmNpf": "15487100000000",
    "enpTastAmt": "455905980000000",
    "enpTdbtAmt": "92228115000000",
    "enpTcptAmt": "363677865000000",
    "enpCptlAmt": "897514000000",
    "fnclDebtRto": "25.3598373385",
    "curCd": "KRW",
}

BS_ITEM = {
    "basDt": "20231231",
    "crno": "1301110006246",
    "bizYear": "2023",
    "fnclDcd": "FS_ifrs-full_ConsolidatedMember",
    "fnclDcdNm": "연결재무제표 [member]",
    "acitId": "ifrs-full_Assets",
    "acitNm": "자산총계",
    "thqrAcitAmt": "0",
    "crtmAcitAmt": "455905980000000",
    "lsqtAcitAmt": "0",
    "pvtrAcitAmt": "448424507000000",
    "bpvtrAcitAmt": "426621158000000",
    "curCd": "KRW",
}

IS_ITEM = {
    "basDt": "20231231",
    "crno": "1301110006246",
    "bizYear": "2023",
    "fnclDcd": "PL_ifrs-full_ConsolidatedMember",
    "fnclDcdNm": "연결재무제표 [member]",
    "acitId": "dart_OperatingIncomeLoss",
    "acitNm": "영업이익(손실)",
    "thqrAcitAmt": "0",
    "crtmAcitAmt": "6566976000000",
    "lsqtAcitAmt": "0",
    "pvtrAcitAmt": "43376630000000",
    "bpvtrAcitAmt": "51633856000000",
    "curCd": "KRW",
}


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture
def summary_response() -> dict:
    return wrap([SUMMARY_ITEM], total=2)


@pytest.fixture
def balance_response() -> dict:
    return wrap([BS_ITEM], total=18)


@pytest.fixture
def income_response() -> dict:
    return wrap([IS_ITEM], total=10)


@pytest.fixture
def empty_response() -> dict:
    return {
        "response": {
            "body": {"items": "", "numOfRows": 10, "pageNo": 1, "totalCount": 0},
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
        }
    }


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("FSC_FINANCIAL_INFO_API_KEY", raising=False)
