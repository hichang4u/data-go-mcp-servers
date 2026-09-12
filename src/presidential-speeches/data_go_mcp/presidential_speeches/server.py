"""MCP server for 대통령기록관 대통령연설기록(연설문)."""

import math
from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from data_go_mcp.core import READ_ONLY, configure_logging, load_api_key, tool_errors

from .api_client import PresidentialSpeechesAPIClient
from .models import Speech2022, Speech2023


load_dotenv()

mcp = MCPServer("Presidential Speech Records")

Page = Annotated[int, Field(description="페이지 번호 (기본값: 1)")]
PerPage = Annotated[int, Field(description="페이지당 결과 수 (기본값: 10)")]
Use2023 = Annotated[
    bool,
    Field(
        description="2023 갱신본 사용 (연설연도 제공). False 면 2022 본 (연설일자 YYYY-MM-DD 제공)"
    ),
]
President = Annotated[Optional[str], Field(description="대통령 이름 (정확히 일치, 예: 노무현)")]


def _speech_dict(speech: Speech2023 | Speech2022) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": speech.id,
        "president": speech.president,
        "title": speech.title,
        "source_url": speech.source_url,
        "location": speech.location,
    }
    if isinstance(speech, Speech2023):
        out["year"] = speech.speech_year
    else:
        out["date"] = speech.speech_date
    return out


@mcp.tool(annotations=READ_ONLY)
async def list_speeches(
    page: Page = 1, per_page: PerPage = 10, use_2023_version: Use2023 = True
) -> dict[str, Any]:
    """대통령 연설문 목록을 조회합니다. List presidential speeches from the archives.

    목록은 오래된 순(1948년부터)이다. 최신 연설은 get_recent_speeches 를 쓴다.
    Returns total_count, page, per_page, data[] (id, president, title, source_url, location,
    year 또는 date).
    """
    async with tool_errors():
        async with PresidentialSpeechesAPIClient() as client:
            if use_2023_version:
                response = await client.get_speeches_2023(page, per_page)
            else:
                response = await client.get_speeches_2022(page, per_page)
    return {
        "total_count": response.total_count,
        "page": response.page,
        "per_page": response.per_page,
        "data": [_speech_dict(s) for s in response.data],
    }


@mcp.tool(annotations=READ_ONLY)
async def search_speeches(
    president: President = None,
    title: Annotated[Optional[str], Field(description="제목에 포함될 키워드 (부분 일치)")] = None,
    year: Annotated[Optional[int], Field(description="연설 연도 (예: 2020)")] = None,
    location: Annotated[
        Optional[str], Field(description="연설 장소 (부분 일치, 예: 국내/국외)")
    ] = None,
    page: Page = 1,
    per_page: PerPage = 10,
) -> dict[str, Any]:
    """대통령 연설문을 검색합니다. Search presidential speeches (server-side filters).

    Returns total_count (조건에 맞는 전체 건수), page, per_page, data[].
    """
    async with tool_errors():
        async with PresidentialSpeechesAPIClient() as client:
            response = await client.search_speeches(
                president=president,
                title=title,
                year=year,
                location=location,
                page=page,
                per_page=per_page,
                use_2023_version=True,
            )
    return {
        "total_count": response.match_count,
        "page": response.page,
        "per_page": response.per_page,
        "data": [_speech_dict(s) for s in response.data],
    }


@mcp.tool(annotations=READ_ONLY)
async def get_recent_speeches(
    president: President = None,
    limit: Annotated[int, Field(description="가져올 연설문 수 (기본값: 5)")] = 5,
) -> dict[str, Any]:
    """최근 대통령 연설문을 조회합니다. Get the most recent presidential speeches.

    목록이 오래된 순이라 전체 건수를 먼저 구한 뒤 마지막 페이지를 읽어 최신순으로 돌려준다.
    Returns count, president, data[] (최신 → 과거).
    """
    async with tool_errors():
        cond = PresidentialSpeechesAPIClient.build_cond(president=president)
        async with PresidentialSpeechesAPIClient() as client:
            probe = await client.get_speeches_2023(page=1, per_page=1, **cond)
            total = probe.match_count
            if total == 0:
                speeches: list[Speech2023] = []
            else:
                last_page = max(1, math.ceil(total / limit))
                response = await client.get_speeches_2023(page=last_page, per_page=limit, **cond)
                speeches = list(reversed(response.data))
    return {
        "count": len(speeches),
        "president": president,
        "data": [_speech_dict(s) for s in speeches],
    }


def main() -> None:
    """Run the MCP server over stdio."""
    logger = configure_logging(__name__)
    try:
        load_api_key(PresidentialSpeechesAPIClient.key_env_prefix)
    except ValueError as e:
        logger.warning("%s — the server will start but tool calls will fail.", e)
    mcp.run()


if __name__ == "__main__":
    main()
