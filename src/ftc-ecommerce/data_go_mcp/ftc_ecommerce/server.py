"""MCP server for FTC E-commerce Sellers API."""

from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from data_go_mcp.core import READ_ONLY, configure_logging, load_api_key, tool_errors

from .api_client import FtcEcommerceAPIClient as Client


load_dotenv()

mcp = MCPServer("FTC E-commerce Sellers")


@mcp.tool(annotations=READ_ONLY)
async def get_online_seller(
    business_number: Annotated[
        Optional[str],
        Field(description="사업자등록번호 10자리 (예: 120-88-00767 또는 1208800767)"),
    ] = None,
    report_number: Annotated[
        Optional[str],
        Field(description="통신판매업 신고번호 (예: 2026-서울광진-1253). 사업자번호 대신 쓴다"),
    ] = None,
    num_of_rows: Annotated[
        int, Field(description="한 페이지 결과 수 (기본값: 10, 최대: 100)")
    ] = 10,
    page_no: Annotated[int, Field(description="페이지 번호 (기본값: 1)")] = 1,
) -> dict[str, Any]:
    """통신판매업 신고 내역을 조회합니다. Look up a mail-order (e-commerce) seller registration.

    온라인으로 물건을 파는 사업자는 통신판매업 신고 의무가 있습니다. 신고번호·신고일·신고기관,
    영업상태(정상영업/직권말소/직권취소), 도메인, 취급품목, 대표자와 연락처가 나옵니다.
    **법인등록번호(corporate_number)가 함께 오므로** 기업 재무제표 조회로 바로 이어집니다.

    사업자번호 또는 신고번호 중 하나가 필요합니다. **상호로는 조회할 수 없습니다** — API 가
    상호 파라미터를 무시하고 전체를 돌려줍니다. 신고하지 않은 사업자는 0건입니다.
    """
    async with tool_errors():
        async with Client() as client:
            return await client.get_online_seller(
                business_number=business_number,
                report_number=report_number,
                num_of_rows=num_of_rows,
                page_no=page_no,
            )


def main() -> None:
    """Run the MCP server over stdio. 로그는 stderr 로만 (stdout 은 프로토콜 채널)."""
    logger = configure_logging(__name__)
    try:
        load_api_key(Client.key_env_prefix)
    except ValueError as e:
        logger.warning("%s — the server will start but tool calls will fail.", e)
    mcp.run()


if __name__ == "__main__":
    main()
