"""MCP server for National Pension Service Business Enrollment API."""

from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from data_go_mcp.core import READ_ONLY, configure_logging, load_api_key, tool_errors

from .api_client import NPSAPIClient


load_dotenv()

mcp = MCPServer("NPS Business Enrollment")

PageNo = Annotated[int, Field(description="페이지 번호 (기본값: 1)")]
Seq = Annotated[int, Field(description="사업장 식별번호 (search_business 결과의 seq)")]


def _add_estimated_salary(item: dict[str, Any], target: dict[str, Any]) -> None:
    """당월고지금액 / 가입자수 / 보험료율(9%) 로 평균 월급을 추정한다."""
    try:
        subscribers = int(item["jnngp_cnt"])
        monthly_amount = int(item["crrmm_ntc_amt"])
    except (KeyError, ValueError, TypeError):
        return
    if subscribers > 0 and monthly_amount > 0:
        target["estimated_avg_monthly_salary"] = round(monthly_amount / subscribers / 0.09)
        target["estimated_avg_monthly_salary_note"] = "추정값 (당월고지금액 기준)"


@mcp.tool(annotations=READ_ONLY)
async def search_business(
    ldong_addr_mgpl_dg_cd: Annotated[
        Optional[str], Field(description="법정동주소 광역시도 코드 (2자리)")
    ] = None,
    ldong_addr_mgpl_sggu_cd: Annotated[
        Optional[str], Field(description="법정동주소 시군구 코드 (5자리)")
    ] = None,
    ldong_addr_mgpl_sggu_emd_cd: Annotated[
        Optional[str], Field(description="법정동주소 읍면동 코드 (8자리)")
    ] = None,
    wkpl_nm: Annotated[Optional[str], Field(description="사업장명 (부분 일치)")] = None,
    bzowr_rgst_no: Annotated[Optional[str], Field(description="사업자등록번호 (앞 6자리)")] = None,
    page_no: PageNo = 1,
    num_of_rows: Annotated[
        int, Field(description="한 페이지 결과 수 (기본값: 100, 최대: 100)")
    ] = 100,
) -> dict[str, Any]:
    """사업장 정보를 조회합니다.

    Search for business enrollment information in the National Pension Service.
    Returns items, page_no, num_of_rows, total_count, message.
    """
    async with tool_errors():
        async with NPSAPIClient() as client:
            result = await client.search_business(
                ldong_addr_mgpl_dg_cd=ldong_addr_mgpl_dg_cd,
                ldong_addr_mgpl_sggu_cd=ldong_addr_mgpl_sggu_cd,
                ldong_addr_mgpl_sggu_emd_cd=ldong_addr_mgpl_sggu_emd_cd,
                wkpl_nm=wkpl_nm,
                bzowr_rgst_no=bzowr_rgst_no,
                page_no=page_no,
                num_of_rows=num_of_rows,
            )
    result["message"] = (
        f"Found {result['total_count']} business(es)"
        if result["items"]
        else "No businesses found matching the criteria"
    )
    return result


@mcp.tool(annotations=READ_ONLY)
async def get_business_detail(
    seq: Seq,
    page_no: PageNo = 1,
    num_of_rows: Annotated[int, Field(description="한 페이지 결과 수 (기본값: 10)")] = 10,
) -> dict[str, Any]:
    """사업장 상세정보를 조회합니다.

    Get detailed information about a specific business enrollment: name, registration
    number, address, industry, registration/withdrawal dates, subscribers, monthly billing
    amount, and an estimated average monthly salary (추정값).
    """
    async with tool_errors():
        async with NPSAPIClient() as client:
            result = await client.get_business_detail(
                seq=seq, page_no=page_no, num_of_rows=num_of_rows
            )
    for item in result["items"]:
        _add_estimated_salary(item, item)
    result["message"] = (
        f"Successfully retrieved details for business #{seq}"
        if result["items"]
        else f"No details found for business #{seq}"
    )
    return result


@mcp.tool(annotations=READ_ONLY)
async def get_period_status(
    seq: Seq,
    data_crt_ym: Annotated[Optional[str], Field(description="조회할 년월 (YYYYMM)")] = None,
    page_no: PageNo = 1,
    num_of_rows: Annotated[int, Field(description="한 페이지 결과 수 (기본값: 10)")] = 10,
) -> dict[str, Any]:
    """사업장의 기간별 현황 정보를 조회합니다.

    Get period-based status: nw_acqzr_cnt (new acquisitions), lss_jnngp_cnt (losses),
    plus estimated_avg_monthly_salary (추정값) taken from the business detail.
    """
    async with tool_errors():
        async with NPSAPIClient() as client:
            result = await client.get_period_status(
                seq=seq, data_crt_ym=data_crt_ym, page_no=page_no, num_of_rows=num_of_rows
            )
            if result["items"]:
                detail = await client.get_business_detail(seq=seq, page_no=1, num_of_rows=1)
                if detail["items"]:
                    _add_estimated_salary(detail["items"][0], result)
    period = f" for {data_crt_ym}" if data_crt_ym else ""
    result["message"] = (
        f"Successfully retrieved period status for business #{seq}{period}"
        if result["items"]
        else f"No period status found for business #{seq}"
    )
    return result


def main() -> None:
    """Run the MCP server over stdio."""
    logger = configure_logging(__name__)
    try:
        load_api_key(NPSAPIClient.key_env_prefix)
    except ValueError as e:
        logger.warning("%s — the server will start but tool calls will fail.", e)
    mcp.run()


if __name__ == "__main__":
    main()
