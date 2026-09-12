"""MCP server for {{ cookiecutter.api_display_name }} API."""

from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from data_go_mcp.core import READ_ONLY, configure_logging, load_api_key, tool_errors

from .api_client import {{ cookiecutter.api_name.replace('-', ' ').title().replace(' ', '') }}APIClient as Client


load_dotenv()

mcp = MCPServer("{{ cookiecutter.api_display_name }}")


@mcp.tool(annotations=READ_ONLY)
async def search_items(
    keyword: Annotated[Optional[str], Field(description="검색어")] = None,
    page_no: Annotated[int, Field(description="페이지 번호 (기본값: 1)")] = 1,
    num_of_rows: Annotated[int, Field(description="한 페이지 결과 수 (기본값: 10)")] = 10,
) -> dict[str, Any]:
    """{{ cookiecutter.api_korean_name }} 을(를) 조회합니다. Search {{ cookiecutter.api_display_name }}.

    Returns items, page_no, num_of_rows, total_count.
    (docstring 의 Args 는 스키마에 실리지 않는다 — 파라미터 설명은 Field(description=) 에.)
    """
    async with tool_errors():  # DataGoAPIError / httpx 오류 / ValueError → ToolError(isError)
        async with Client() as client:
            return await client.get_items(keyword=keyword, page_no=page_no, num_of_rows=num_of_rows)


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
