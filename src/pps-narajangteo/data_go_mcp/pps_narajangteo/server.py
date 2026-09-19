"""MCP server for 나라장터 공공데이터개방표준서비스 (Public Procurement Service Open Data)."""

from datetime import datetime, timedelta
from typing import Annotated, Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from data_go_mcp.core import (
    READ_ONLY,
    configure_logging,
    load_api_key,
    normalize_items,
    tool_errors,
)

from .api_client import PpsNarajangteoAPIClient


load_dotenv()

mcp = MCPServer("나라장터 공공데이터개방표준서비스")

BUSINESS_TYPE_NAMES = {"1": "물품", "2": "외자", "3": "공사", "5": "용역"}

Date = Annotated[Optional[str], Field(description="날짜 (YYYY-MM-DD 또는 YYYYMMDD)")]
NumOfRows = Annotated[int, Field(description="한 페이지 결과 수 (기본값: 10, 최대: 999)")]
PageNo = Annotated[int, Field(description="페이지 번호 (기본값: 1)")]


def format_datetime_for_api(dt: Optional[str] = None, is_end: bool = False) -> str:
    """날짜/시간을 API 형식(YYYYMMDDHHMM)으로 변환. ``None`` 이면 오늘."""
    if not dt:
        return datetime.now().strftime("%Y%m%d2359" if is_end else "%Y%m%d0000")
    clean = dt.replace("-", "").replace(":", "").replace(" ", "")
    if len(clean) == 8 and clean.isdigit():
        return clean + ("2359" if is_end else "0000")
    if len(clean) == 12 and clean.isdigit():
        return clean
    raise ValueError(f"잘못된 날짜/시간 형식: {dt}")


def parse_business_type(business_type: str) -> str:
    """업무구분(물품/외자/공사/용역 또는 1/2/3/5)을 코드로."""
    by_name = {name: code for code, name in BUSINESS_TYPE_NAMES.items()}
    return by_name.get(business_type, business_type)


def _range(
    start_date: Optional[str], end_date: Optional[str], default_days: int = 0
) -> tuple[str, str]:
    """툴 공통 날짜 범위 계산. 시작일이 없으면 오늘(또는 최근 default_days일)."""
    if not start_date:
        end = datetime.now()
        start = end - timedelta(days=default_days)
        return start.strftime("%Y%m%d0000"), end.strftime("%Y%m%d2359")
    return (
        format_datetime_for_api(start_date, is_end=False),
        format_datetime_for_api(end_date or start_date, is_end=True),
    )


def _previous_weekday_range() -> tuple[str, str]:
    """직전 평일 하루 (낙찰 개찰은 평일에만, 당일분은 진행 중이라 불완전)."""
    day = datetime.now() - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day.strftime("%Y%m%d0000"), day.strftime("%Y%m%d2359")


def _span_days(start_dt: str, end_dt: str) -> int:
    """YYYYMMDDhhmm 범위가 걸치는 날 수 (같은 날이면 1)."""
    start = datetime.strptime(start_dt[:8], "%Y%m%d")
    end = datetime.strptime(end_dt[:8], "%Y%m%d")
    return (end - start).days + 1


# get_bid_detail 이 훑는 최대 페이지 (999건씩). 공고는 하루 1,100건 이상 (2026-09 기준)
DETAIL_SCAN_PAGES = 12
DETAIL_DEFAULT_DAYS = 7


def _page(body: dict[str, Any], page_no: int, num_of_rows: int, **extra: Any) -> dict[str, Any]:
    return {
        "success": True,
        "items": normalize_items(body),
        "total_count": body.get("totalCount", 0),
        "page_no": body.get("pageNo", page_no),
        "num_of_rows": body.get("numOfRows", num_of_rows),
        **extra,
    }


@mcp.tool(annotations=READ_ONLY)
async def search_bid_announcements(
    start_date: Date = None,
    end_date: Date = None,
    num_of_rows: NumOfRows = 10,
    page_no: PageNo = 1,
) -> dict[str, Any]:
    """나라장터 입찰공고정보를 검색합니다. Search bid announcements in the G2B marketplace.

    검색 기간은 최대 1개월. 날짜를 지정하지 않으면 오늘 하루를 검색합니다.
    Returns items (raw camelCase fields such as bidNtceNo, bidNtceNm, ntceInsttNm, opengDate),
    total_count, page_no, num_of_rows, search_period.
    """
    async with tool_errors():
        start_dt, end_dt = _range(start_date, end_date)
        async with PpsNarajangteoAPIClient() as client:
            body = await client.get_bid_announcements(start_dt, end_dt, num_of_rows, page_no)
    return _page(body, page_no, num_of_rows, search_period=f"{start_dt[:8]} ~ {end_dt[:8]}")


@mcp.tool(annotations=READ_ONLY)
async def search_successful_bids(
    business_type: Annotated[
        str, Field(description="업무구분: 물품/외자/공사/용역 또는 코드 1/2/3/5")
    ] = "1",
    start_date: Date = None,
    end_date: Date = None,
    num_of_rows: NumOfRows = 10,
    page_no: PageNo = 1,
) -> dict[str, Any]:
    """나라장터 낙찰정보를 검색합니다. Search successful bids in the G2B marketplace.

    개찰일시 기준으로 **하루**만 조회할 수 있습니다 (API 제한). 날짜를 지정하지 않으면 직전 평일을
    검색합니다 (당일 개찰은 진행 중이라 불완전). 하루에 물품 2만·공사 9만 건 규모이니 num_of_rows 와
    page_no 로 나눠 보세요.
    """
    async with tool_errors():
        code = parse_business_type(business_type)
        start_dt, end_dt = (
            _range(start_date, end_date) if start_date else _previous_weekday_range()
        )
        if start_dt[:8] != end_dt[:8]:
            raise ValueError(
                f"낙찰정보는 하루 단위로만 조회할 수 있습니다: {start_dt[:8]} ~ {end_dt[:8]}. "
                "start_date 하나만 지정하세요."
            )
        async with PpsNarajangteoAPIClient() as client:
            body = await client.get_successful_bids(code, start_dt, end_dt, num_of_rows, page_no)
    return _page(
        body,
        page_no,
        num_of_rows,
        business_type=BUSINESS_TYPE_NAMES.get(code, code),
        search_period=f"{start_dt[:8]} ~ {end_dt[:8]}",
    )


@mcp.tool(annotations=READ_ONLY)
async def search_contracts(
    start_date: Date = None,
    end_date: Date = None,
    institution_type: Annotated[
        Optional[str], Field(description="기관구분코드 (1: 계약기관, 2: 수요기관)")
    ] = None,
    institution_code: Annotated[Optional[str], Field(description="기관코드 (7자리)")] = None,
    num_of_rows: NumOfRows = 10,
    page_no: PageNo = 1,
) -> dict[str, Any]:
    """나라장터 계약정보를 검색합니다. Search contracts in the G2B marketplace.

    계약체결일자 기준. 검색 기간은 **최대 7일** (API 제한). 날짜를 지정하지 않으면 오늘을 검색합니다.
    """
    async with tool_errors():
        start_dt, end_dt = _range(start_date, end_date)
        if _span_days(start_dt, end_dt) > 7:
            raise ValueError(
                f"계약정보는 최대 7일까지 조회할 수 있습니다: {start_dt[:8]} ~ {end_dt[:8]}. "
                "기간을 나눠 호출하세요."
            )
        start_d, end_d = start_dt[:8], end_dt[:8]
        async with PpsNarajangteoAPIClient() as client:
            body = await client.get_contracts(
                start_d, end_d, institution_type, institution_code, num_of_rows, page_no
            )
    return _page(
        body,
        page_no,
        num_of_rows,
        search_period=f"{start_d} ~ {end_d}",
        institution_filter=(
            {"type": institution_type, "code": institution_code}
            if institution_type or institution_code
            else None
        ),
    )


@mcp.tool(annotations=READ_ONLY)
async def get_bid_detail(
    bid_notice_no: Annotated[str, Field(description="입찰공고번호 (예: R25BK00933743)")],
    start_date: Date = None,
    end_date: Date = None,
) -> dict[str, Any]:
    """특정 입찰공고의 상세정보를 조회합니다. Get one bid announcement by its notice number.

    이 API에는 공고번호 단건 조회가 없어 공고일시 범위(기본: 최근 7일)를 999건씩 최대 12페이지
    (약 1만 2천 건, 열흘치) 훑어 찾습니다. 공고는 하루 1,100건 이상이고 날짜순으로 오지 않으므로,
    공고일을 알면 start_date(=end_date) 로 그날만 지정하세요 — 가장 빠르고 확실합니다.
    """
    async with tool_errors():
        start_dt, end_dt = _range(start_date, end_date, default_days=DETAIL_DEFAULT_DAYS)
        async with PpsNarajangteoAPIClient() as client:
            for page_no in range(1, DETAIL_SCAN_PAGES + 1):
                body = await client.get_bid_announcements(start_dt, end_dt, 999, page_no)
                items = normalize_items(body)
                for item in items:
                    if item.get("bidNtceNo") == bid_notice_no:
                        return {
                            "success": True,
                            "data": item,
                            "message": f"입찰공고번호 {bid_notice_no}의 상세정보",
                        }
                if len(items) < 999:
                    break
        raise ToolError(
            f"입찰공고번호 {bid_notice_no}를 {start_dt[:8]} ~ {end_dt[:8]} 범위"
            f"(최대 {DETAIL_SCAN_PAGES * 999}건)에서 찾을 수 없습니다. "
            "공고일을 알면 start_date 로 그날을 지정하세요."
        )


def main() -> None:
    """Run the MCP server over stdio."""
    logger = configure_logging(__name__)
    try:
        load_api_key(PpsNarajangteoAPIClient.key_env_prefix)
    except ValueError as e:
        logger.warning("%s — the server will start but tool calls will fail.", e)
    mcp.run()


if __name__ == "__main__":
    main()
