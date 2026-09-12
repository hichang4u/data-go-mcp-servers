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


# 금융위원회_기업기본정보 (GetCorpBasicInfoService_V2) — 2026-09-12 실응답 발췌.
# 같은 crno 가 유효기간(fstOpegDt~lastOpegDt)별 스냅샷으로 여러 번 온다.
CORP_BASE = "https://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2"

_SAMSUNG_LATEST = {
    "crno": "1301110006246",
    "corpNm": "삼성전자(주)",
    "corpEnsnNm": "SAMSUNG ELECTRONICS CO,.LTD",
    "enpPbanCmpyNm": "삼성전자",
    "enpRprFnm": "전영현, 노태문",
    "corpRegMrktDcd": "P",
    "corpRegMrktDcdNm": "유가",
    "corpDcd": "",
    "corpDcdNm": "",
    "bzno": "1248100998",
    "enpOzpno": "16677",
    "enpBsadr": "경기도 수원시 영통구  삼성로 129 (매탄동)",
    "enpDtadr": "",
    "enpHmpgUrl": "www.samsung.com/sec",
    "enpTlno": "02-2255-0114",
    "enpFxno": "031-200-7538",
    "sicNm": "",
    "enpEstbDt": "19690113",
    "enpStacMm": "12",
    "enpXchgLstgDt": "75/06/11",
    "enpXchgLstgAbolDt": "",
    "enpKosdaqLstgDt": "",
    "enpKosdaqLstgAbolDt": "",
    "enpKrxLstgDt": "",
    "enpKrxLstgAbolDt": "",
    "smenpYn": "",
    "enpMntrBnkNm": "",
    "enpEmpeCnt": "128881",
    "empeAvgCnwkTermCtt": "13.7",
    "enpPn1AvgSlryAmt": "158000000",
    "actnAudpnNm": "삼정회계법인",
    "audtRptOpnnCtt": "적정의견",
    "enpMainBizNm": "",
    "fssCorpUnqNo": "00126380",
    "fssCorpChgDtm": "2025/12/01",
    "fstOpegDt": "20260311",
    "lastOpegDt": "20260911",
}
_SAMSUNG_OLDER = {
    **_SAMSUNG_LATEST,
    "actnAudpnNm": "",
    "audtRptOpnnCtt": "",
    "fstOpegDt": "20260310",
    "lastOpegDt": "20260310",
}
_CHEONGPYEONG = {
    "crno": "2845110008637",
    "corpNm": "청평삼성전자(주)",
    "corpEnsnNm": "CHEONGPYEONG SAMSUNG ELECTRONICS CO.,LTD",
    "enpPbanCmpyNm": "",
    "enpRprFnm": "김정호",
    "corpRegMrktDcd": "",
    "corpRegMrktDcdNm": "",
    "corpDcd": "",
    "corpDcdNm": "",
    "bzno": "1328173319",
    "enpOzpno": "476813",
    "enpBsadr": "경기 양평군 서종면",
    "enpDtadr": "756-1",
    "enpHmpgUrl": "",
    "enpTlno": "82-031-774-1405",
    "enpFxno": "031-585-3250",
    "sicNm": "",
    "enpEstbDt": "",
    "enpStacMm": "",
    "enpXchgLstgDt": "",
    "enpXchgLstgAbolDt": "",
    "enpKosdaqLstgDt": "",
    "enpKosdaqLstgAbolDt": "",
    "enpKrxLstgDt": "",
    "enpKrxLstgAbolDt": "",
    "smenpYn": "",
    "enpMntrBnkNm": "",
    "enpEmpeCnt": "0",
    "empeAvgCnwkTermCtt": "",
    "enpPn1AvgSlryAmt": "0",
    "actnAudpnNm": "",
    "audtRptOpnnCtt": "",
    "enpMainBizNm": "",
    "fssCorpUnqNo": "",
    "fssCorpChgDtm": "",
    "fstOpegDt": "20200517",
    "lastOpegDt": "20200517",
}


@pytest.fixture
def corp_base_url() -> str:
    return CORP_BASE


@pytest.fixture
def corp_response() -> dict:
    """옛 스냅샷이 먼저 오도록 섞어 둔다 — 최신 선택이 순서에 의존하지 않게."""
    return wrap([_SAMSUNG_OLDER, _CHEONGPYEONG, _SAMSUNG_LATEST], total=20)
