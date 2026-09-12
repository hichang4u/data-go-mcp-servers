"""MCP server for 안전보건공단 물질안전보건자료(MSDS)."""

from typing import Annotated, Any, Iterable, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from data_go_mcp.core import READ_ONLY, configure_logging, load_api_key, tool_errors

from .api_client import MsdsChemicalInfoAPIClient, detect_search_type
from .models import SECTION_TITLES, MsdsSection, SearchType


load_dotenv()

mcp = MCPServer("MSDS Chemical Info")

ChemId = Annotated[
    str, Field(description="화학물질ID 6자리 (search_chemicals 결과의 chem_id; 짧으면 0으로 채움)")
]
SECTION_LIST = "\n".join(f"{n}: {t}" for n, t in SECTION_TITLES.items())


def _chem_id(value: str) -> str:
    return value.strip().zfill(6)


def _section_dict(section: MsdsSection) -> dict[str, Any]:
    out: dict[str, Any] = {
        "title": section.section_title,
        "content": section.get_formatted_content(),
    }
    if section.error:
        out["error"] = section.error
    return out


async def _grouped(chem_id: str, numbers: Iterable[int]) -> dict[str, Any]:
    """섹션 묶음 조회 툴 공통 본문."""
    async with tool_errors():
        cid = _chem_id(chem_id)
        async with MsdsChemicalInfoAPIClient() as client:
            sections = await client.get_sections(cid, numbers)
    result: dict[str, Any] = {"chem_id": cid}
    for n, section in sections.items():
        result[f"section_{n}"] = _section_dict(section)
    return result


@mcp.tool(annotations=READ_ONLY)
async def search_chemicals(
    search_term: Annotated[
        str,
        Field(
            description="검색어: 국문명, CAS No.(71-43-2), UN No.(UN1114), KE No.(KE-02150), EN No."
        ),
    ],
    search_type: Annotated[
        Optional[str],
        Field(
            description="검색 구분 (생략 시 자동 감지): KOREAN_NAME, CAS_NO, UN_NO, KE_NO, EN_NO"
        ),
    ] = None,
    page_no: Annotated[int, Field(description="페이지 번호 (기본값: 1)")] = 1,
    num_of_rows: Annotated[
        int, Field(description="한 페이지 결과 수 (기본값: 10, 최대: 100)")
    ] = 10,
) -> dict[str, Any]:
    """화학물질을 검색합니다. Search chemicals by name or identifier (CAS/UN/KE/EN No.).

    Returns search_type_used, items[] (chem_id, chem_name_kor, cas_no, un_no, ke_no, en_no,
    last_date), total_count, page_no, num_of_rows. 상세 조회에는 chem_id 를 쓴다.
    """
    async with tool_errors():
        if search_type:
            try:
                kind = SearchType[search_type.upper()]
            except KeyError:
                raise ValueError(
                    f"Invalid search type: {search_type}. "
                    "Valid options: KOREAN_NAME, CAS_NO, UN_NO, KE_NO, EN_NO"
                ) from None
        else:
            kind = detect_search_type(search_term)
        async with MsdsChemicalInfoAPIClient() as client:
            resp = await client.search_chemicals(
                search_term, kind, page_no=page_no, num_of_rows=min(num_of_rows, 100)
            )
    return {
        "search_type_used": kind.name,
        "items": [
            {
                "chem_id": i.chem_id,
                "chem_name_kor": i.chem_name_kor,
                "cas_no": i.cas_no,
                "un_no": i.un_no,
                "ke_no": i.ke_no,
                "en_no": i.en_no,
                "last_date": i.last_date,
            }
            for i in resp.items
        ],
        "total_count": resp.total_count,
        "page_no": resp.page_no,
        "num_of_rows": resp.num_of_rows,
    }


@mcp.tool(annotations=READ_ONLY)
async def get_chemical_safety_summary(chem_id: ChemId) -> dict[str, Any]:
    """화학물질의 핵심 안전정보를 조회합니다 (섹션 1-4: 제품·회사, 유해성, 구성성분, 응급조치).

    Get essential safety information (sections 1-4).
    """
    return await _grouped(chem_id, range(1, 5))


@mcp.tool(annotations=READ_ONLY)
async def get_chemical_handling_info(chem_id: ChemId) -> dict[str, Any]:
    """화학물질의 취급·보호 정보를 조회합니다 (섹션 5-8: 화재, 누출, 취급·저장, 보호구).

    Get handling and protection information (sections 5-8).
    """
    return await _grouped(chem_id, range(5, 9))


@mcp.tool(annotations=READ_ONLY)
async def get_chemical_properties(chem_id: ChemId) -> dict[str, Any]:
    """화학물질의 물성·독성 정보를 조회합니다 (섹션 9-12: 물리화학적 특성, 안정성, 독성, 환경).

    Get physical/chemical properties and toxicity (sections 9-12).
    """
    return await _grouped(chem_id, range(9, 13))


@mcp.tool(annotations=READ_ONLY)
async def get_chemical_regulatory_info(chem_id: ChemId) -> dict[str, Any]:
    """화학물질의 규제·폐기 정보를 조회합니다 (섹션 13-16: 폐기, 운송, 법적 규제, 기타).

    Get regulatory and disposal information (sections 13-16).
    """
    return await _grouped(chem_id, range(13, 17))


@mcp.tool(annotations=READ_ONLY)
async def get_chemical_section(
    chem_id: ChemId,
    section_number: Annotated[int, Field(description=f"섹션 번호 1-16:\n{SECTION_LIST}")],
) -> dict[str, Any]:
    """화학물질 MSDS 의 특정 섹션을 조회합니다. Get one MSDS section (1-16)."""
    async with tool_errors():
        cid = _chem_id(chem_id)
        async with MsdsChemicalInfoAPIClient() as client:
            section = await client.get_chemical_detail(cid, section_number)
    return {
        "chem_id": cid,
        "section_number": section_number,
        "title": section.section_title,
        "content": section.get_formatted_content(),
    }


@mcp.tool(annotations=READ_ONLY)
async def get_complete_msds(chem_id: ChemId) -> dict[str, Any]:
    """화학물질의 전체 MSDS (16개 섹션)를 조회합니다. Get the complete MSDS (all 16 sections).

    16회 호출을 동시에 보낸다. 일부 섹션이 실패하면 그 섹션에 error 를 넣고 나머지는 반환한다.
    """
    async with tool_errors():
        cid = _chem_id(chem_id)
        async with MsdsChemicalInfoAPIClient() as client:
            sections = await client.get_sections(cid, range(1, 17), tolerate_errors=True)
    return {
        "chem_id": cid,
        "sections": {
            f"section_{n}": {"number": n, **_section_dict(s)} for n, s in sections.items()
        },
    }


def main() -> None:
    """Run the MCP server over stdio."""
    logger = configure_logging(__name__)
    try:
        load_api_key(MsdsChemicalInfoAPIClient.key_env_prefix)
    except ValueError as e:
        logger.warning("%s — the server will start but tool calls will fail.", e)
    mcp.run()


if __name__ == "__main__":
    main()
