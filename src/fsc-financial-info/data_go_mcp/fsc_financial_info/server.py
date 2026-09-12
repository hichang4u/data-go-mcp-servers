#!/usr/bin/env python3
"""
MCP server for FSC Corporate Financial Information API.
금융위원회 기업 재무정보 API를 위한 MCP 서버.
"""

import logging
import os
import sys
from decimal import Decimal
from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from .api_client import FSCFinancialAPIClient


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Server information
SERVER_NAME = "data-go-mcp.fsc-financial-info"
SERVER_VERSION = "0.1.1"

mcp = MCPServer(SERVER_NAME, version=SERVER_VERSION)

CRNO_DESC = "법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)"
BIZ_YEAR_DESC = "사업연도 (예: 2023) | Business year (e.g., 2023)"
PAGE_NO_DESC = "페이지 번호 (기본값: 1) | Page number (default: 1)"
NUM_OF_ROWS_DESC = "한 페이지 결과 수 (기본값: 10, 최대: 100) | Number of rows per page (default: 10, max: 100)"

NO_API_KEY_MSG = (
    "Error: API_KEY environment variable is not set. "
    "Please set your API key to use this service."
)


def decimal_to_str(value: Any) -> Any:
    """Convert Decimal values to string for JSON serialization."""
    if isinstance(value, Decimal):
        return str(value)
    elif isinstance(value, dict):
        return {k: decimal_to_str(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [decimal_to_str(item) for item in value]
    return value


def format_financial_amount(amount: Optional[Decimal], currency: str = "KRW") -> str:
    """Format financial amount with proper units."""
    if amount is None:
        return "N/A"

    # Convert to float for calculations
    value = float(amount)

    # Format based on size
    if abs(value) >= 1_000_000_000_000:  # Trillion
        formatted = f"{value / 1_000_000_000_000:,.2f}조"
    elif abs(value) >= 100_000_000:  # Hundred million
        formatted = f"{value / 100_000_000:,.2f}억"
    elif abs(value) >= 10_000:  # Ten thousand
        formatted = f"{value / 10_000:,.0f}만"
    else:
        formatted = f"{value:,.0f}"

    if currency == "KRW":
        return f"{formatted}원"
    return f"{formatted} {currency}"


def _format_error(name: str, e: Exception) -> str:
    """원본 저수준 서버의 오류 문구를 그대로 유지한다."""
    if isinstance(e, ValueError):
        msg = str(e)
        return f"API 오류: {msg}" if "API Error" in msg else f"입력값 오류: {msg}"
    if isinstance(e, ConnectionError):
        return f"연결 오류: {e}. 네트워크 연결을 확인해주세요."
    logger.error(f"Unexpected error in tool {name}: {e}", exc_info=True)
    return f"처리 중 오류가 발생했습니다: {e}"


def _format_account_items(title: str, response: Any, abs_pct: bool) -> str:
    """재무상태표/손익계산서 공통 포맷."""
    result_lines = [f"{title} 조회 결과 (총 {response.total_count}건)\n"]
    current_crno = None
    for item in response.items:
        if current_crno != item.crno:
            current_crno = item.crno
            result_lines.extend([
                f"\n{'='*50}",
                f"법인등록번호: {item.crno}",
                f"사업연도: {item.biz_year}",
                f"기준일자: {item.bas_dt}",
                f"재무제표구분: {item.fncl_dcd_nm or item.fncl_dcd or 'N/A'}",
                "\n📊 계정과목별 금액:",
            ])
        lines = [
            f"\n  [{item.acit_nm or item.acit_id}]",
            f"    • 당기: {format_financial_amount(item.crtm_acit_amt, item.cur_cd or 'KRW')}",
            f"    • 전기: {format_financial_amount(item.pvtr_acit_amt, item.cur_cd or 'KRW')}",
        ]
        if item.crtm_acit_amt and item.pvtr_acit_amt:
            change = float(item.crtm_acit_amt - item.pvtr_acit_amt)
            base = float(item.pvtr_acit_amt)
            if abs_pct:
                base = abs(base)
            change_pct = (change / base * 100) if item.pvtr_acit_amt != 0 else 0
            lines.append(
                f"    • 증감: {format_financial_amount(Decimal(str(change)), item.cur_cd or 'KRW')} ({change_pct:+.1f}%)"
            )
        result_lines.extend(lines)
    return "\n".join(result_lines)


@mcp.tool()
async def get_summary_financial_statement(
    crno: Annotated[Optional[str], Field(description=CRNO_DESC)] = None,
    biz_year: Annotated[Optional[str], Field(description=BIZ_YEAR_DESC)] = None,
    page_no: Annotated[int, Field(description=PAGE_NO_DESC)] = 1,
    num_of_rows: Annotated[int, Field(description=NUM_OF_ROWS_DESC)] = 10,
) -> str:
    """기업의 요약 재무제표를 조회합니다. 매출액, 영업이익, 당기순이익, 자산, 부채 등 주요 재무지표를 확인할 수 있습니다. | Get summary financial statements including revenue, operating profit, net income, assets, and liabilities.

    Args:
        crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
        biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)
        page_no: 페이지 번호 (기본값: 1) | Page number (default: 1)
        num_of_rows: 한 페이지 결과 수 (기본값: 10, 최대: 100) | Number of rows per page (default: 10, max: 100)
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        return NO_API_KEY_MSG
    try:
        async with FSCFinancialAPIClient(api_key=api_key) as client:
            response = await client.get_summary_financial_statement(
                crno=crno, biz_year=biz_year, page_no=page_no, num_of_rows=num_of_rows
            )
    except Exception as e:
        return _format_error("get_summary_financial_statement", e)

    if not response.items:
        return "조회된 재무제표가 없습니다. 법인등록번호와 사업연도를 확인해주세요."

    result_lines = [f"📊 요약 재무제표 조회 결과 (총 {response.total_count}건)\n"]
    for item in response.items:
        cur = item.cur_cd or "KRW"
        result_lines.extend([
            f"\n{'='*50}",
            f"법인등록번호: {item.crno}",
            f"사업연도: {item.biz_year}",
            f"기준일자: {item.bas_dt}",
            f"재무제표구분: {item.fncl_dcd_nm or item.fncl_dcd or 'N/A'}",
            f"통화: {cur}",
            "\n💰 주요 재무지표:",
            f"  • 매출액: {format_financial_amount(item.enp_sale_amt, cur)}",
            f"  • 영업이익: {format_financial_amount(item.enp_bzop_pft, cur)}",
            f"  • 당기순이익: {format_financial_amount(item.enp_crtm_npf, cur)}",
            f"  • 총자산: {format_financial_amount(item.enp_tast_amt, cur)}",
            f"  • 총부채: {format_financial_amount(item.enp_tdbt_amt, cur)}",
            f"  • 총자본: {format_financial_amount(item.enp_tcpt_amt, cur)}",
            f"  • 자본금: {format_financial_amount(item.enp_cptl_amt, cur)}",
            f"  • 부채비율: {float(item.fncl_debt_rto):.2f}%" if item.fncl_debt_rto else "  • 부채비율: N/A",
        ])
    return "\n".join(result_lines)


@mcp.tool()
async def get_balance_sheet(
    crno: Annotated[Optional[str], Field(description=CRNO_DESC)] = None,
    biz_year: Annotated[Optional[str], Field(description=BIZ_YEAR_DESC)] = None,
    page_no: Annotated[int, Field(description=PAGE_NO_DESC)] = 1,
    num_of_rows: Annotated[int, Field(description=NUM_OF_ROWS_DESC)] = 10,
) -> str:
    """기업의 재무상태표(대차대조표)를 조회합니다. 자산, 부채, 자본의 세부 계정과목별 금액을 확인할 수 있습니다. | Get balance sheet with detailed account items for assets, liabilities, and equity.

    Args:
        crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
        biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)
        page_no: 페이지 번호 (기본값: 1) | Page number (default: 1)
        num_of_rows: 한 페이지 결과 수 (기본값: 10, 최대: 100) | Number of rows per page (default: 10, max: 100)
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        return NO_API_KEY_MSG
    try:
        async with FSCFinancialAPIClient(api_key=api_key) as client:
            response = await client.get_balance_sheet(
                crno=crno, biz_year=biz_year, page_no=page_no, num_of_rows=num_of_rows
            )
    except Exception as e:
        return _format_error("get_balance_sheet", e)

    if not response.items:
        return "조회된 재무상태표가 없습니다. 법인등록번호와 사업연도를 확인해주세요."
    return _format_account_items("📋 재무상태표", response, abs_pct=False)


@mcp.tool()
async def get_income_statement(
    crno: Annotated[Optional[str], Field(description=CRNO_DESC)] = None,
    biz_year: Annotated[Optional[str], Field(description=BIZ_YEAR_DESC)] = None,
    page_no: Annotated[int, Field(description=PAGE_NO_DESC)] = 1,
    num_of_rows: Annotated[int, Field(description=NUM_OF_ROWS_DESC)] = 10,
) -> str:
    """기업의 손익계산서를 조회합니다. 매출, 비용, 이익 등의 세부 계정과목별 금액을 확인할 수 있습니다. | Get income statement with detailed account items for revenue, expenses, and profit.

    Args:
        crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
        biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)
        page_no: 페이지 번호 (기본값: 1) | Page number (default: 1)
        num_of_rows: 한 페이지 결과 수 (기본값: 10, 최대: 100) | Number of rows per page (default: 10, max: 100)
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        return NO_API_KEY_MSG
    try:
        async with FSCFinancialAPIClient(api_key=api_key) as client:
            response = await client.get_income_statement(
                crno=crno, biz_year=biz_year, page_no=page_no, num_of_rows=num_of_rows
            )
    except Exception as e:
        return _format_error("get_income_statement", e)

    if not response.items:
        return "조회된 손익계산서가 없습니다. 법인등록번호와 사업연도를 확인해주세요."
    return _format_account_items("💹 손익계산서", response, abs_pct=True)


@mcp.tool()
async def search_company_financial_info(
    crno: Annotated[str, Field(description=CRNO_DESC)],
    biz_year: Annotated[str, Field(description=BIZ_YEAR_DESC)],
) -> str:
    """법인등록번호로 기업의 전체 재무정보를 통합 조회합니다. 요약 재무제표, 재무상태표, 손익계산서를 한번에 가져옵니다. | Search comprehensive financial information by corporate registration number, including summary, balance sheet, and income statement.

    Args:
        crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
        biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        return NO_API_KEY_MSG
    if not crno or not biz_year:
        return "Error: 법인등록번호(crno)와 사업연도(biz_year)는 필수 입력 항목입니다."

    result_lines = ["🏢 기업 재무정보 통합 조회\n"]
    async with FSCFinancialAPIClient(api_key=api_key) as client:
        try:
            summary_response = await client.get_summary_financial_statement(
                crno=crno, biz_year=biz_year, num_of_rows=5
            )
            if summary_response.items:
                result_lines += [f"\n{'='*60}", "📊 요약 재무제표", "=" * 60]
                for item in summary_response.items:
                    result_lines.extend([
                        f"재무제표구분: {item.fncl_dcd_nm or 'N/A'}",
                        f"• 매출액: {format_financial_amount(item.enp_sale_amt)}",
                        f"• 영업이익: {format_financial_amount(item.enp_bzop_pft)}",
                        f"• 당기순이익: {format_financial_amount(item.enp_crtm_npf)}",
                        f"• 총자산: {format_financial_amount(item.enp_tast_amt)}",
                        f"• 총부채: {format_financial_amount(item.enp_tdbt_amt)}",
                        f"• 부채비율: {float(item.fncl_debt_rto):.2f}%" if item.fncl_debt_rto else "• 부채비율: N/A",
                        "",
                    ])
        except Exception as e:
            logger.error(f"Failed to get summary statement: {e}")
            result_lines.append(f"❌ 요약 재무제표 조회 실패: {e}")

        for title, method, fail_label in (
            ("📋 재무상태표 주요 항목", client.get_balance_sheet, "재무상태표"),
            ("💹 손익계산서 주요 항목", client.get_income_statement, "손익계산서"),
        ):
            try:
                resp = await method(crno=crno, biz_year=biz_year, num_of_rows=10)
                if resp.items:
                    result_lines += [f"\n{'='*60}", title, "=" * 60]
                    for item in resp.items[:5]:
                        result_lines.append(f"• {item.acit_nm}: {format_financial_amount(item.crtm_acit_amt)}")
                    if resp.total_count > 5:
                        result_lines.append(f"  ... 외 {resp.total_count - 5}개 항목")
                    result_lines.append("")
            except Exception as e:
                logger.error(f"Failed to get {fail_label}: {e}")
                result_lines.append(f"❌ {fail_label} 조회 실패: {e}")

    return "\n".join(result_lines)


def main():
    """Main entry point."""
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    if not os.getenv("API_KEY"):
        logger.warning(
            "API_KEY not found in environment variables. "
            "The server will start but API calls will fail without a valid key."
        )
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
