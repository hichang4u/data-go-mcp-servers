"""실제 data.go.kr 호출 — `API_KEY` 가 있을 때만 (scripts/check_apis.py 의 pytest 판).

로컬에서 ``uv run pytest -m integration`` 으로 실행. CI 에는 키가 없어 자동 skip 된다.
"""

import os
import sys

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from mcp.types import TextContent


pytestmark = pytest.mark.integration

# (모듈, 툴, 인자, 응답 텍스트에 반드시 포함될 문자열)
CALLS = [
    (
        "nps_business_enrollment",
        "search_business",
        {"wkpl_nm": "삼성전자", "num_of_rows": 1},
        '"total_count"',
    ),
    (
        "nps_business_enrollment",
        "find_region_code",
        {"name": "서울특별시 강남구 역삼동"},
        '"sgg_cd": "680"',
    ),
    (
        "nps_business_enrollment",
        "get_insurance_status",
        {"bzno": "1248100998", "insurance": "고용", "num_of_rows": 1},
        '"insurance": "고용"',
    ),
    (
        "nts_business_verification",
        "check_business_status",
        {"business_numbers": "1208800767"},
        "계속사업자",
    ),
    ("fsc_financial_info", "find_corp_number", {"bzno": "1248100998"}, '"crno": "1301110006246"'),
    (
        "fsc_financial_info",
        "get_stock_price",
        {"srtn_cd": "005930", "num_of_rows": 1},
        '"itms_nm": "삼성전자"',
    ),
    ("pps_narajangteo", "search_contracts", {"num_of_rows": 1}, '"success": true'),
    (
        "fsc_financial_info",
        "get_market_index",
        {"index_name": "코스피", "num_of_rows": 1},
        '"index_name": "코스피"',
    ),
    (
        "fsc_financial_info",
        "get_etf_price",
        {"item_name": "KODEX 200", "num_of_rows": 1},
        '"nav"',
    ),
    (
        "molit_realestate",
        "search_property_trades",
        {"region_code": "11680", "deal_ym": "202608", "num_of_rows": 3},
        '"deal_amount"',
    ),
    (
        "pps_narajangteo",
        "get_procurement_company",
        {"business_number": "111-81-26895"},
        '"registered": true',
    ),
    (
        "pps_narajangteo",
        "check_procurement_sanctions",
        {"business_number": "327-81-00184"},
        '"restricted_now"',
    ),
    (
        "molit_realestate",
        "get_building_register",
        {"region_code": "1168010500", "bun": "1", "ji": "1"},
        '"total_floor_area"',
    ),
    (
        "molit_realestate",
        "search_property_rents",
        {"region_code": "11680", "deal_ym": "202608", "num_of_rows": 3},
        '"rent_type"',
    ),
    (
        "pps_narajangteo",
        "find_bid_winners",
        {"company_name": "주식회사", "start_date": "2026-08-26", "end_date": "2026-08-26"},
        '"scanned_count"',
    ),
    (
        "work24_jobs",
        "search_job_postings",
        {"business_number": "5038169211", "num_of_rows": 2},
        '"business_number": "5038169211"',
    ),
    ("bok_ecos", "get_key_statistics", {"class_name": "환율", "num_of_rows": 10}, '"class_name"'),
    (
        "bok_ecos",
        "get_statistic_data",
        {
            "stat_code": "722Y001",
            "cycle": "M",
            "start_time": "202401",
            "end_time": "202403",
            "item_code1": "0101000",
            "num_of_rows": 10,
        },
        '"202401"',
    ),
    # 낙찰은 하루 범위만 — 기본(오늘/직전 금요일)이 07 없이 통과하는지
    (
        "pps_narajangteo",
        "search_successful_bids",
        {"business_type": "용역", "num_of_rows": 1},
        '"search_period"',
    ),
    (
        "fsc_financial_info",
        "get_summary_financial_statement",
        {"crno": "1301110006246", "biz_year": "2023", "num_of_rows": 1},
        "요약 재무제표",
    ),
    ("presidential_speeches", "search_speeches", {"president": "노무현", "per_page": 1}, "노무현"),
    ("msds_chemical_info", "search_chemicals", {"search_term": "71-43-2"}, "벤젠"),
    ("dart_disclosure", "get_company", {"corp_code": "00126380"}, '"jurir_no": "1301110006246"'),
]

# data.go.kr 키로는 안 되는 서버: 서버별 키가 없으면 그 항목만 skip
KEY_ENV = {
    "dart_disclosure": "DART_DISCLOSURE_API_KEY",
    "bok_ecos": "BOK_ECOS_API_KEY",
    "work24_jobs": "WORK24_API_KEY",
}


@pytest.mark.parametrize(
    "module, tool, args, expected", CALLS, ids=[f"{c[0]}:{c[1]}" for c in CALLS]
)
async def test_live_tool_call(module: str, tool: str, args: dict, expected: str) -> None:
    key_env = KEY_ENV.get(module)
    if key_env and not os.getenv(key_env):
        pytest.skip(f"{key_env} not set")
    params = StdioServerParameters(
        command=sys.executable, args=["-m", f"data_go_mcp.{module}.server"], env=dict(os.environ)
    )
    async with Client(params) as client:
        result = await client.call_tool(tool, args)
    (content,) = result.content
    assert isinstance(content, TextContent)
    assert result.is_error is False, content.text
    assert expected in content.text
