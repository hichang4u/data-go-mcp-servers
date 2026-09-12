"""nts 테스트 공용 fixture — 2026-09-12 odcloud 실제 응답 형태."""

import pytest


BASE = "https://api.odcloud.kr/api/nts-businessman/v1"

STATUS_ACTIVE = {
    "b_no": "1208800767",
    "b_stt": "계속사업자",
    "b_stt_cd": "01",
    "tax_type": "부가가치세 일반과세자",
    "tax_type_cd": "01",
    "end_dt": "",
    "utcc_yn": "N",
    "tax_type_change_dt": "",
    "invoice_apply_dt": "",
    "rbf_tax_type": "해당없음",
    "rbf_tax_type_cd": "99",
}

STATUS_UNKNOWN = {
    "b_no": "0000000000",
    "b_stt": "",
    "b_stt_cd": "",
    "tax_type": "국세청에 등록되지 않은 사업자등록번호입니다.",
    "tax_type_cd": "",
    "end_dt": "",
    "utcc_yn": "",
    "tax_type_change_dt": "",
    "invoice_apply_dt": "",
    "rbf_tax_type": "",
    "rbf_tax_type_cd": "",
}

VALIDATE_MISMATCH = {
    "request_cnt": 1,
    "status_code": "OK",
    "data": [
        {
            "b_no": "1208800767",
            "valid": "02",
            "valid_msg": "확인할 수 없습니다.",
            "request_param": {
                "b_no": "1208800767",
                "start_dt": "20000101",
                "p_nm": "홍길동",
                "p_nm2": "",
                "b_nm": "",
                "corp_no": "",
                "b_type": "",
                "b_sector": "",
                "b_adr": "",
            },
        }
    ],
}

VALIDATE_MATCH = {
    "request_cnt": 1,
    "valid_cnt": 1,
    "status_code": "OK",
    "data": [
        {
            "b_no": "1208800767",
            "valid": "01",
            "request_param": VALIDATE_MISMATCH["data"][0]["request_param"],
            "status": STATUS_ACTIVE,
        }
    ],
}


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture
def status_response() -> dict:
    return {
        "request_cnt": 2,
        "match_cnt": 1,
        "status_code": "OK",
        "data": [dict(STATUS_ACTIVE), dict(STATUS_UNKNOWN)],
    }


@pytest.fixture
def validate_match() -> dict:
    return VALIDATE_MATCH


@pytest.fixture
def validate_mismatch() -> dict:
    return VALIDATE_MISMATCH


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("NTS_BUSINESS_VERIFICATION_API_KEY", raising=False)
