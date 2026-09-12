"""6개 서버를 실제 stdio 서브프로세스로 띄워 list_tools 가 동작하는지 확인하는 스모크 테스트.

서버 구현 방식(MCPServer / 저수준 Server)과 무관하게 클라이언트 관점에서 검증한다.
"""

import os
import sys

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


SERVERS = {
    "nps_business_enrollment": {
        "search_business",
        "get_business_detail",
        "get_period_status",
        "find_region_code",
        "get_insurance_status",
    },
    "nts_business_verification": {
        "validate_business",
        "check_business_status",
        "batch_validate_businesses",
    },
    "pps_narajangteo": {
        "search_bid_announcements",
        "search_successful_bids",
        "search_contracts",
        "get_bid_detail",
    },
    "fsc_financial_info": {
        "get_summary_financial_statement",
        "get_balance_sheet",
        "get_income_statement",
        "search_company_financial_info",
        "find_corp_number",
        "get_corp_outline",
        "get_stock_price",
        "search_stock_items",
    },
    "presidential_speeches": {"list_speeches", "search_speeches", "get_recent_speeches"},
    "msds_chemical_info": {
        "search_chemicals",
        "get_chemical_safety_summary",
        "get_chemical_handling_info",
        "get_chemical_properties",
        "get_chemical_regulatory_info",
        "get_chemical_section",
        "get_complete_msds",
    },
}


@pytest.mark.parametrize("module", sorted(SERVERS))
async def test_server_lists_tools_over_stdio(module: str) -> None:
    """서버가 stdio 로 기동되고 기대한 툴 이름을 전부 노출한다."""
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", f"data_go_mcp.{module}.server"],
        env={**os.environ, "API_KEY": "test-key"},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
    names = {t.name for t in result.tools}
    assert names == SERVERS[module]


@pytest.mark.parametrize("module", sorted(SERVERS))
async def test_server_starts_without_api_key(module: str, tmp_path) -> None:
    """API 키가 없어도 기동되고 list_tools 가 된다 (경고는 stderr 로만 — stdout 오염 시 여기서 죽는다)."""
    env = {k: v for k, v in os.environ.items() if not k.endswith("API_KEY")}
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", f"data_go_mcp.{module}.server"],
        env=env,
        cwd=tmp_path,  # 저장소 루트의 .env 를 load_dotenv 가 읽지 못하게
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
    assert {t.name for t in result.tools} == SERVERS[module]
