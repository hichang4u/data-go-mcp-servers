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
        "nts_business_verification",
        "check_business_status",
        {"business_numbers": "1208800767"},
        "계속사업자",
    ),
    ("pps_narajangteo", "search_contracts", {"num_of_rows": 1}, '"success": true'),
    (
        "fsc_financial_info",
        "get_summary_financial_statement",
        {"crno": "1301110006246", "biz_year": "2023", "num_of_rows": 1},
        "요약 재무제표",
    ),
    ("presidential_speeches", "search_speeches", {"president": "노무현", "per_page": 1}, "노무현"),
    ("msds_chemical_info", "search_chemicals", {"search_term": "71-43-2"}, "벤젠"),
]


@pytest.mark.parametrize("module, tool, args, expected", CALLS, ids=[c[0] for c in CALLS])
async def test_live_tool_call(module: str, tool: str, args: dict, expected: str) -> None:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", f"data_go_mcp.{module}.server"], env=dict(os.environ)
    )
    async with Client(params) as client:
        result = await client.call_tool(tool, args)
    (content,) = result.content
    assert isinstance(content, TextContent)
    assert result.is_error is False, content.text
    assert expected in content.text
