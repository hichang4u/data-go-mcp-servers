"""MCP server for 한국은행 경제통계시스템(ECOS).

기준금리·환율·물가 같은 거시 통계를 통계표 코드로 조회한다. 코드를 모를 때는
``find_statistic_table`` → ``get_statistic_items`` → ``get_statistic_data`` 순으로 좁힌다.
"""

from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from data_go_mcp.core import READ_ONLY, configure_logging, load_api_key, tool_errors

from .api_client import BokEcosAPIClient
from .models import CYCLES


load_dotenv()

mcp = MCPServer("BOK ECOS")

CYCLE_HELP = ", ".join(f"{code}={desc}" for code, desc in CYCLES.items())

KEY_STATISTIC_ROWS = 200  # "100대 지표" 는 실제로 101건

NumOfRows = Annotated[
    int, Field(description="한 페이지 결과 수 (기본값: 100. sample 키는 10을 넘기면 오류)")
]
PageNo = Annotated[int, Field(description="페이지 번호 (기본값: 1)")]


@mcp.tool(annotations=READ_ONLY)
async def find_statistic_table(
    keyword: Annotated[
        str, Field(description="통계표 이름에 포함된 말 (예: 기준금리, 환율, 소비자물가)")
    ],
    cycle: Annotated[Optional[str], Field(description=f"주기로 좁히기: {CYCLE_HELP}")] = None,
    limit: Annotated[int, Field(description="최대 결과 수 (기본값: 20)")] = 20,
) -> dict[str, Any]:
    """통계표 코드를 이름으로 찾습니다. Find ECOS statistic table codes by name.

    다른 툴은 모두 통계표 코드(stat_code)를 요구하므로 여기서 먼저 찾습니다. ECOS 에는 이름 검색
    API 가 없어 전체 목록(약 844건)을 받아 거르며, 목록은 프로세스 안에 한 번만 받아 둡니다.
    조회할 수 없는 분류 노드(SRCH_YN=N)는 제외합니다.
    """
    async with tool_errors():
        async with BokEcosAPIClient() as client:
            hits = await client.find_tables(keyword, cycle, limit)
    return {
        "items": hits,
        "total_count": len(hits),
        "keyword": keyword,
        "message": "stat_code 를 get_statistic_items / get_statistic_data 에 넘기세요",
    }


@mcp.tool(annotations=READ_ONLY)
async def get_statistic_items(
    stat_code: Annotated[str, Field(description="통계표 코드 (예: 722Y001)")],
    num_of_rows: NumOfRows = 100,
) -> dict[str, Any]:
    """통계표의 세부항목과 조회 가능 기간을 봅니다. List items and searchable periods.

    항목 코드(item_code)와 주기(cycle)별 start_time/end_time 을 돌려줍니다. 같은 항목이 주기마다
    한 줄씩 오고 시점 형식도 주기를 따르므로(월 199901, 분기 2002Q4), 여기 값을 그대로
    get_statistic_data 에 넘기면 됩니다.
    """
    async with tool_errors():
        async with BokEcosAPIClient() as client:
            result = await client.get_items(stat_code, num_of_rows)
    return {**result, "stat_code": stat_code}


@mcp.tool(annotations=READ_ONLY)
async def get_statistic_data(
    stat_code: Annotated[str, Field(description="통계표 코드 (예: 722Y001)")],
    cycle: Annotated[str, Field(description=f"주기: {CYCLE_HELP}")],
    start_time: Annotated[str, Field(description="시작 시점. 주기 형식에 맞춘다 (예: 202401)")],
    end_time: Annotated[str, Field(description="종료 시점. 주기 형식에 맞춘다 (예: 202412)")],
    item_code1: Annotated[
        Optional[str], Field(description="항목 코드 1. 생략하면 통계표의 모든 항목")
    ] = None,
    item_code2: Annotated[Optional[str], Field(description="항목 코드 2")] = None,
    item_code3: Annotated[Optional[str], Field(description="항목 코드 3")] = None,
    item_code4: Annotated[Optional[str], Field(description="항목 코드 4")] = None,
    num_of_rows: NumOfRows = 100,
    page_no: PageNo = 1,
) -> dict[str, Any]:
    """통계 시계열을 조회합니다. Get an ECOS statistic time series.

    시점(time)과 값(value)을 시계열로 돌려줍니다. 항목 코드를 생략하면 통계표의 모든 항목이 오므로
    건수가 빠르게 늘어납니다 — 항목을 아는 경우 지정하세요 (최대 4개). 조회 가능 기간은
    get_statistic_items 가 알려줍니다. 해당 기간에 자료가 없으면 빈 결과입니다.
    """
    async with tool_errors():
        codes = [item_code1, item_code2, item_code3, item_code4]
        async with BokEcosAPIClient() as client:
            result = await client.search(
                stat_code, cycle, start_time, end_time, codes, num_of_rows, page_no
            )
    return {
        **result,
        "stat_code": stat_code,
        "cycle": cycle,
        "search_period": f"{start_time} ~ {end_time}",
        "page_no": page_no,
    }


@mcp.tool(annotations=READ_ONLY)
async def get_key_statistics(
    class_name: Annotated[
        Optional[str],
        Field(description="지표 분류로 좁히기 (예: 환율, 금리, 국민계정, 물가). 부분 일치"),
    ] = None,
    num_of_rows: Annotated[
        int, Field(description="한 페이지 결과 수 (기본값: 200 — 지표가 101건이라 한 번에 받는다)")
    ] = KEY_STATISTIC_ROWS,
) -> dict[str, Any]:
    """100대 통계지표의 최신값을 봅니다. Get the latest values of 100 key indicators.

    환율·기준금리·물가 같은 대표 지표(101건)를 코드 없이 바로 봅니다. 각 항목의 time 은 지표마다 기준
    시점이 달라(일/월) 그대로 돌려줍니다. 시계열이 필요하면 get_statistic_data 를 쓰세요.
    """
    async with tool_errors():
        async with BokEcosAPIClient() as client:
            result = await client.get_key_statistics(num_of_rows)
    if class_name:
        needle = class_name.strip()
        items = [i for i in result["items"] if needle in (i.get("class_name") or "")]
        return {"items": items, "total_count": len(items), "class_name": class_name}
    return result


@mcp.tool(annotations=READ_ONLY)
async def search_term(
    word: Annotated[str, Field(description="찾을 통계 용어 (예: 기준금리, 경상수지)")],
    num_of_rows: NumOfRows = 100,
) -> dict[str, Any]:
    """통계 용어의 뜻을 찾습니다. Look up an economic statistics term.

    한국은행 통계용어사전의 설명을 돌려줍니다.
    """
    async with tool_errors():
        async with BokEcosAPIClient() as client:
            result = await client.get_word(word, num_of_rows)
    return {**result, "word": word}


def main() -> None:
    """Run the MCP server over stdio."""
    logger = configure_logging(__name__)
    try:
        load_api_key(
            BokEcosAPIClient.key_env_prefix,
            shared=BokEcosAPIClient.shared_key,
            key_url=BokEcosAPIClient.key_url,
        )
    except ValueError as e:
        logger.warning("%s — the server will start but tool calls will fail.", e)
    mcp.run()


if __name__ == "__main__":
    main()
