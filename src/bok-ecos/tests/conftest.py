"""bok-ecos 테스트 공용 fixture — 2026-09-29 ECOS sample 키 실제 응답."""

import pytest


BASE = "https://ecos.bok.or.kr/api"

TABLE_LIST = {
    "StatisticTableList": {
        "list_total_count": 844,
        "row": [
            {
                "P_STAT_CODE": "*",
                "STAT_CODE": "0000000001",
                "STAT_NAME": "1. 통화/금융",
                "CYCLE": None,
                "SRCH_YN": "N",
                "ORG_NAME": None,
            },
            {
                "P_STAT_CODE": "0000000622",
                "STAT_CODE": "102Y004",
                "STAT_NAME": "1.1.1.1.1. 본원통화 구성내역(평잔, 계절조정계열)",
                "CYCLE": "M",
                "SRCH_YN": "Y",
                "ORG_NAME": None,
            },
            {
                "P_STAT_CODE": "0000000633",
                "STAT_CODE": "722Y001",
                "STAT_NAME": "1.3.1. 한국은행 기준금리 및 여수신금리",
                "CYCLE": "M",
                "SRCH_YN": "Y",
                "ORG_NAME": None,
            },
            {
                "P_STAT_CODE": "0000000650",
                "STAT_CODE": "151Y001",
                "STAT_NAME": "1.2.4.1.1. 가계신용(업권별, 분기)",
                "CYCLE": "Q",
                "SRCH_YN": "Y",
                "ORG_NAME": None,
            },
        ],
    }
}

KEY_STATISTICS = {
    "KeyStatisticList": {
        "list_total_count": 101,
        "row_count": 3,
        "row": [
            {
                "CLASS_NAME": "환율",
                "KEYSTAT_NAME": "원/달러 환율(종가)",
                "DATA_VALUE": "1356.7",
                "CYCLE": "20260929",
                "UNIT_NAME": "원",
            },
            {
                "CLASS_NAME": "환율",
                "KEYSTAT_NAME": "원/엔(100엔) 환율(매매기준율)",
                "DATA_VALUE": "863.9",
                "CYCLE": "20260929",
                "UNIT_NAME": "원",
            },
            {
                "CLASS_NAME": "금리",
                "KEYSTAT_NAME": "한국은행 기준금리",
                "DATA_VALUE": "2.50",
                "CYCLE": "202609",
                "UNIT_NAME": "연%",
            },
        ],
    }
}

ITEM_LIST = {
    "StatisticItemList": {
        "list_total_count": 48,
        "row": [
            {
                "STAT_CODE": "722Y001",
                "STAT_NAME": "1.3.1. 한국은행 기준금리 및 여수신금리",
                "GRP_CODE": "Group1",
                "GRP_NAME": "계정항목",
                "ITEM_CODE": "0101000",
                "ITEM_NAME": "한국은행 기준금리",
                "P_ITEM_CODE": None,
                "P_ITEM_NAME": None,
                "CYCLE": "A",
                "START_TIME": "1999",
                "END_TIME": "2025",
                "DATA_CNT": 27,
                "UNIT_NAME": "연%",
                "WEIGHT": None,
            },
            {
                "STAT_CODE": "722Y001",
                "STAT_NAME": "1.3.1. 한국은행 기준금리 및 여수신금리",
                "GRP_CODE": "Group1",
                "GRP_NAME": "계정항목",
                "ITEM_CODE": "0101000",
                "ITEM_NAME": "한국은행 기준금리",
                "P_ITEM_CODE": None,
                "P_ITEM_NAME": None,
                "CYCLE": "M",
                "START_TIME": "199901",
                "END_TIME": "202609",
                "DATA_CNT": 333,
                "UNIT_NAME": "연%",
                "WEIGHT": None,
            },
        ],
    }
}

SEARCH = {
    "StatisticSearch": {
        "list_total_count": 27,
        "row": [
            {
                "STAT_CODE": "722Y001",
                "STAT_NAME": "1.3.1. 한국은행 기준금리 및 여수신금리",
                "ITEM_CODE1": "0101000",
                "ITEM_NAME1": "한국은행 기준금리",
                "ITEM_CODE2": None,
                "ITEM_NAME2": None,
                "ITEM_CODE3": None,
                "ITEM_NAME3": None,
                "ITEM_CODE4": None,
                "ITEM_NAME4": None,
                "UNIT_NAME": "연%",
                "WGT": None,
                "TIME": "202401",
                "DATA_VALUE": "3.5",
            },
            {
                "STAT_CODE": "722Y001",
                "STAT_NAME": "1.3.1. 한국은행 기준금리 및 여수신금리",
                "ITEM_CODE1": "0102000",
                "ITEM_NAME1": "정부대출금금리",
                "ITEM_CODE2": None,
                "ITEM_NAME2": None,
                "ITEM_CODE3": None,
                "ITEM_NAME3": None,
                "ITEM_CODE4": None,
                "ITEM_NAME4": None,
                "UNIT_NAME": "연%",
                "WGT": None,
                "TIME": "202401",
                "DATA_VALUE": "1.75",
            },
        ],
    }
}

WORD = {
    "StatisticWord": {
        "list_total_count": 1,
        "row": [
            {
                "WORD": "기준금리",
                "CONTENT": (
                    "한국은행이 금융기관과 환매조건부증권(RP) 매매, 자금조정 예금 및 대출 등의 "
                    "거래를 할 때 기준이 되는 정책금리"
                ),
            }
        ],
    }
}

ERROR_KEY = {
    "RESULT": {
        "CODE": "INFO-100",
        "MESSAGE": "인증키가 유효하지 않습니다. 인증키를 확인하십시오! 인증키가 없는 경우 인증키를 신청하십시오!",
    }
}

ERROR_NO_DATA = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}

ERROR_COUNT = {
    "RESULT": {
        "CODE": "ERROR-301",
        "MESSAGE": (
            "조회건수 값의 타입이 유효하지 않습니다. 조회건수 값을 확인하십시오!\n"
            " 조회건수 값의 타입이 유효하지 않으면 오류를 발생합니다. \n"
            " sample은 최대 10건 이내에서 호출이 가능합니다."
        ),
    }
}


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture
def table_list() -> dict:
    return TABLE_LIST


@pytest.fixture
def key_statistics() -> dict:
    return KEY_STATISTICS


@pytest.fixture
def item_list() -> dict:
    return ITEM_LIST


@pytest.fixture
def search_result() -> dict:
    return SEARCH


@pytest.fixture
def word() -> dict:
    return WORD


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("BOK_ECOS_API_KEY", "test-key")
    monkeypatch.delenv("API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _clear_table_cache():
    from data_go_mcp.bok_ecos.api_client import clear_table_cache

    clear_table_cache()
    yield
    clear_table_cache()
