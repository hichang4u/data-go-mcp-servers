"""MCP server for 고용24 채용정보 (옛 워크넷).

사업자등록번호로 채용공고를 바로 찾을 수 있어, 국세청·금융위·근로복지공단·조달청 조회와
같은 번호로 이어진다. 지역코드는 nps 의 ``find_region_code`` 결과를 그대로 받는다.
"""

from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from data_go_mcp.core import READ_ONLY, configure_logging, load_api_key, tool_errors

from .api_client import DEFAULT_INFO_SERVICE, MAX_DISPLAY, Work24JobsAPIClient


load_dotenv()

mcp = MCPServer("Work24 Jobs")


@mcp.tool(annotations=READ_ONLY)
async def search_job_postings(
    business_number: Annotated[
        Optional[str],
        Field(description="사업자등록번호 10자리 (하이픈 허용). 회사별 조회에 가장 정확하다"),
    ] = None,
    keyword: Annotated[
        Optional[str],
        Field(description="검색어. 공고 전반을 훑으므로 회사명으로 쓰면 무관한 공고도 섞인다"),
    ] = None,
    region_code: Annotated[
        Optional[str],
        Field(
            description=(
                "지역코드. 법정동코드 앞 5자리(예: 11680 강남구) 또는 10자리. "
                "시도 전체는 11000 처럼. 모르면 nps 서버의 find_region_code 로 찾는다"
            )
        ),
    ] = None,
    occupation: Annotated[
        Optional[str], Field(description="직종 코드 6자리 (예: 155500 환경공학 기술자)")
    ] = None,
    min_pay: Annotated[
        Optional[int], Field(description="최저 임금 하한 (원 단위 연봉, 예: 40000000)")
    ] = None,
    num_of_rows: Annotated[
        int, Field(description=f"한 페이지 결과 수 (기본값: 20, 최대: {MAX_DISPLAY})")
    ] = 20,
    page_no: Annotated[int, Field(description="페이지 번호 (기본값: 1)")] = 1,
) -> dict[str, Any]:
    """고용24 채용공고를 검색합니다. Search job postings on 고용24 (formerly WorkNet).

    **사업자등록번호로 바로 조회됩니다** — 어떤 회사가 지금 어떤 자리를, 얼마에 뽑는지 봅니다.
    조건을 하나도 주지 않으면 전국 공고 전체(5만 건 이상)가 되므로 최소 하나는 필요합니다.
    임금은 원 단위이며 max_salary 가 0이면 상한 미지정입니다. 상세 내용(담당 업무, 자격증,
    기업 규모)은 wanted_auth_no 를 get_job_posting 에 넘기세요.
    """
    async with tool_errors():
        async with Work24JobsAPIClient() as client:
            result = await client.search_jobs(
                business_number=business_number,
                keyword=keyword,
                region_code=region_code,
                occupation=occupation,
                min_pay=min_pay,
                num_of_rows=num_of_rows,
                page_no=page_no,
            )
    return {**result, "page_no": page_no}


@mcp.tool(annotations=READ_ONLY)
async def get_job_posting(
    wanted_auth_no: Annotated[
        str, Field(description="채용공고 번호 (search_job_postings 의 wanted_auth_no)")
    ],
    info_service: Annotated[
        str,
        Field(
            description=(
                "정보제공처. 목록 결과의 info_service 를 그대로 넘긴다 "
                f"(기본값: {DEFAULT_INFO_SERVICE})"
            )
        ),
    ] = DEFAULT_INFO_SERVICE,
) -> dict[str, Any]:
    """채용공고 상세를 조회합니다. Get one job posting in full.

    담당 업무·자격증·전공·우대조건과 함께 **기업 정보(종업원 수, 자본금, 연 매출액, 기업 규모)**를
    돌려줍니다. 비상장 회사는 금융위 재무정보에 없는 경우가 많아, 여기가 규모를 알 수 있는
    유일한 공개 자료일 때가 있습니다.
    """
    async with tool_errors():
        async with Work24JobsAPIClient() as client:
            return await client.get_job(wanted_auth_no, info_service)


def main() -> None:
    """Run the MCP server over stdio."""
    logger = configure_logging(__name__)
    try:
        load_api_key(
            Work24JobsAPIClient.key_env_prefix,
            shared=Work24JobsAPIClient.shared_key,
            key_url=Work24JobsAPIClient.key_url,
        )
    except ValueError as e:
        logger.warning("%s — the server will start but tool calls will fail.", e)
    mcp.run()


if __name__ == "__main__":
    main()
