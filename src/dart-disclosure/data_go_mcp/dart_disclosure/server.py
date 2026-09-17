"""MCP server for 금융감독원 전자공시(OpenDART)."""

from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from data_go_mcp.core import READ_ONLY, configure_logging, load_api_key, tool_errors

from .api_client import MAX_PAGE_COUNT
from .api_client import DartDisclosureAPIClient as Client
from .corp_codes import load_snapshot, search_corp_codes


load_dotenv()

mcp = MCPServer("DART Disclosure")

CORP_CODE_DESC = (
    "DART 고유번호 (8자리 숫자; 모르면 find_corp_code 로 조회) | DART corp_code (8 digits)"
)
REPRT_CODE_DESC = (
    "보고서 코드: 11011 사업보고서(기본), 11012 반기보고서, 11013 1분기보고서, 11014 3분기보고서 | "
    "Report type"
)
YEAR_DESC = "사업연도 YYYY (예: 2024). 2015년 이후만 제공 | Business year"
DEFAULT_DOC_CHARS = 20_000


@mcp.tool(annotations=READ_ONLY)
async def find_corp_code(
    query: Annotated[
        str,
        Field(
            description="회사명(한글·영문, 부분 일치) 또는 6자리 종목코드 | Company name (partial) or 6-digit stock code"
        ),
    ],
    listed_only: Annotated[
        bool,
        Field(description="상장사(종목코드 있는 회사)만 | Only listed companies (default: false)"),
    ] = False,
    limit: Annotated[int, Field(description="최대 결과 수 (기본값: 20)", ge=1, le=100)] = 20,
) -> dict[str, Any]:
    """회사명 또는 종목코드로 DART 고유번호(corp_code)를 찾습니다. 다른 툴의 corp_code 입력에 씁니다. | Find the 8-digit DART corp_code by company name or stock code.

    Returns items (corp_code, corp_name, stock_code, corp_eng_name), total_count, snapshot_date.
    Exact name match ranks first, then prefix, then partial; listed companies before unlisted.
    Searches a bundled snapshot of all ~120k DART-registered companies (no API call);
    snapshot_date is when it was taken, so companies registered after that are missing.
    Same-name companies are common (e.g. 11 "신한") — check stock_code or use get_company to confirm.
    """
    async with tool_errors():
        snapshot = load_snapshot()
        result = search_corp_codes(query, snapshot.entries, listed_only=listed_only, limit=limit)
        return {**result, "snapshot_date": snapshot.generated}


@mcp.tool(annotations=READ_ONLY)
async def get_company(
    corp_code: Annotated[str, Field(description=CORP_CODE_DESC)],
) -> dict[str, Any]:
    """DART 고유번호로 기업 개황(정식명칭, 대표자, 법인등록번호, 사업자등록번호, 주소, 설립일, 결산월 등)을 조회합니다. | Get a company profile by corp_code.

    Returns corp_name, corp_name_eng, stock_code, ceo_nm, corp_cls/corp_cls_name, jurir_no (13-digit
    corporate registration number — usable as crno in fsc-financial-info tools), bizr_no, adres,
    hm_url, induty_code, est_dt, acc_mt.
    """
    async with tool_errors():
        async with Client() as client:
            company = await client.get_company(corp_code)
        if company is None:
            raise ToolError(f"고유번호 {corp_code} 에 해당하는 회사가 없습니다")
        return company


@mcp.tool(annotations=READ_ONLY)
async def list_disclosures(
    corp_code: Annotated[Optional[str], Field(description=CORP_CODE_DESC)] = None,
    bgn_de: Annotated[
        Optional[str],
        Field(
            description=(
                "검색 시작 접수일 YYYYMMDD (생략 시 corp_code 있으면 1년 전, 없으면 30일 전) | Start date"
            )
        ),
    ] = None,
    end_de: Annotated[
        Optional[str], Field(description="검색 종료 접수일 YYYYMMDD (생략 시 오늘) | End date")
    ] = None,
    pblntf_ty: Annotated[
        Optional[str],
        Field(
            description=(
                "공시유형: A 정기공시, B 주요사항보고, C 발행공시, D 지분공시, E 기타공시, "
                "F 외부감사관련, G 펀드공시, H 자산유동화, I 거래소공시, J 공정위공시 | Disclosure type"
            )
        ),
    ] = None,
    page_no: Annotated[int, Field(description="페이지 번호 (기본값: 1)", ge=1)] = 1,
    page_count: Annotated[
        int,
        Field(
            description=f"한 페이지 결과 수 (기본값: 10, 최대 {MAX_PAGE_COUNT})",
            ge=1,
            le=MAX_PAGE_COUNT,
        ),
    ] = 10,
) -> dict[str, Any]:
    """공시 목록을 조회합니다 (접수일 내림차순). 사업보고서·주요사항보고서·지분공시 등의 접수번호를 얻는 데 씁니다. | List DART disclosures (newest first).

    Returns items (rcept_no, corp_name, report_nm, flr_nm, rcept_dt, rm), page_no, page_count,
    total_count, total_page. Pass rcept_no to get_disclosure_document for the full text.
    Without corp_code the date range must be 3 months or less (API limit). Omitting bgn_de
    searches the last year (with corp_code) or last 30 days (without), counted back from end_de.
    """
    async with tool_errors():
        async with Client() as client:
            return await client.list_disclosures(
                corp_code=corp_code,
                bgn_de=bgn_de,
                end_de=end_de,
                pblntf_ty=pblntf_ty,
                page_no=page_no,
                page_count=page_count,
            )


@mcp.tool(annotations=READ_ONLY)
async def get_key_accounts(
    corp_code: Annotated[str, Field(description=CORP_CODE_DESC)],
    bsns_year: Annotated[str, Field(description=YEAR_DESC)],
    reprt_code: Annotated[str, Field(description=REPRT_CODE_DESC)] = "11011",
    fs_div: Annotated[
        Optional[str],
        Field(
            description="CFS 연결재무제표 / OFS 별도재무제표 (생략 시 둘 다) | Consolidated or separate"
        ),
    ] = None,
) -> dict[str, Any]:
    """정기보고서의 주요 재무계정(자산·부채·자본 총계, 매출액, 영업이익, 당기순이익 등)을 당기·전기·전전기로 조회합니다. | Get key financial accounts (assets, liabilities, equity, revenue, operating income, net income) for the current and two prior periods.

    Returns items (fs_div, sj_div, account_nm, thstrm_amount, frmtrm_amount, bfefrmtrm_amount,
    thstrm_dt, currency). Amounts are integers in KRW. Roughly 20–30 rows; use
    get_financial_statements for every account line.
    """
    async with tool_errors():
        async with Client() as client:
            return await client.get_key_accounts(
                corp_code, bsns_year, reprt_code=reprt_code, fs_div=fs_div
            )


@mcp.tool(annotations=READ_ONLY)
async def get_financial_statements(
    corp_code: Annotated[str, Field(description=CORP_CODE_DESC)],
    bsns_year: Annotated[str, Field(description=YEAR_DESC)],
    reprt_code: Annotated[str, Field(description=REPRT_CODE_DESC)] = "11011",
    fs_div: Annotated[
        str,
        Field(description="CFS 연결재무제표(기본) / OFS 별도재무제표 | Consolidated or separate"),
    ] = "CFS",
    sj_div: Annotated[
        Optional[str],
        Field(
            description=(
                "재무제표 종류로 필터: BS 재무상태표, IS 손익계산서, CIS 포괄손익계산서, "
                "CF 현금흐름표, SCE 자본변동표 (생략 시 전부) | Statement type filter"
            )
        ),
    ] = None,
) -> dict[str, Any]:
    """정기보고서의 전체 재무제표를 XBRL 계정 단위로 조회합니다 (재무상태표·손익계산서·포괄손익계산서·현금흐름표·자본변동표). | Get full financial statements (all XBRL account lines).

    Returns items (sj_div, account_id, account_nm, thstrm_amount, frmtrm_amount, bfefrmtrm_amount,
    thstrm_add_amount for quarterly cumulative, currency). Amounts are integers in KRW.
    A full annual report is ~200 rows; pass sj_div to keep the response small.
    Listed companies from business year 2015 onward only.
    """
    async with tool_errors():
        async with Client() as client:
            return await client.get_financial_statements(
                corp_code, bsns_year, reprt_code=reprt_code, fs_div=fs_div, sj_div=sj_div
            )


@mcp.tool(annotations=READ_ONLY)
async def get_disclosure_document(
    rcept_no: Annotated[
        str, Field(description="접수번호 (14자리; list_disclosures 의 rcept_no) | Receipt number")
    ],
    offset: Annotated[int, Field(description="본문 시작 문자 위치 (기본값: 0)", ge=0)] = 0,
    max_chars: Annotated[
        int,
        Field(description=f"돌려줄 최대 문자 수 (기본값: {DEFAULT_DOC_CHARS})", ge=1, le=200_000),
    ] = DEFAULT_DOC_CHARS,
) -> dict[str, Any]:
    """공시 원문을 텍스트로 조회합니다. 사업보고서는 수십만 자라 offset/max_chars 로 나눠 읽습니다. | Get the full text of a disclosure document, paged by offset/max_chars.

    Returns rcept_no, file_name, attachment_files, text, offset, next_offset, total_chars, truncated.
    When truncated is true, call again with offset=next_offset (the document is cached in-process,
    so paging does not re-download it).
    """
    async with tool_errors():
        async with Client() as client:
            doc = await client.get_document(rcept_no)
        text: str = doc.pop("text")
        total = len(text)
        end = min(offset + max_chars, total)
        return {
            **doc,
            "text": text[offset:end],
            "offset": offset,
            "next_offset": end,
            "total_chars": total,
            "truncated": end < total,
        }


def main() -> None:
    """Run the MCP server over stdio. 로그는 stderr 로만 (stdout 은 프로토콜 채널)."""
    logger = configure_logging(__name__)
    try:
        load_api_key(Client.key_env_prefix, shared=Client.shared_key, key_url=Client.key_url)
    except ValueError as e:
        logger.warning("%s — the server will start but tool calls will fail.", e)
    mcp.run()


if __name__ == "__main__":
    main()
