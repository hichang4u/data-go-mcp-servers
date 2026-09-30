"""API client for 나라장터 — 공공데이터개방표준서비스와 낙찰정보서비스.

낙찰업체 조회(``find_bid_winners``)만 낙찰정보서비스(``as/ScsbidInfoService``)를 쓴다.
2026-09-30 실호출로 확인한 것:

- 개방표준서비스의 낙찰정보에는 **업체 정보가 아예 없다**. 낙찰업체 사업자번호·상호는
  낙찰정보서비스의 ``getScsbidListSttus*`` 응답에만 있다
- 그런데 ``bidwinnrBizno``/``bidwinnrNm`` 을 요청 파라미터로 주면 **무시된다** (전체가 온다)
  → 기간을 999건씩 훑어 클라이언트에서 거른다
- ``PPSSrch`` 가 붙은 오퍼레이션은 부분집합이다 (같은 날 53건 vs 357건) → 전수 쪽을 쓴다
- ``inqryDiv=1`` 은 등록일시, ``inqryDiv=2`` 가 **개찰일시** 기준이다
- 기간 한도는 1개월. 용역 1개월 전수가 4~8페이지, 15~35초 (오래된 달일수록 건수가 많다)
"""

import datetime as dt
import re
from typing import Any, Mapping, Optional

from data_go_mcp.core import BaseDataGoClient, DataGoAPIError, normalize_items


ERROR_WRAPPER = "nkoneps.com.response.ResponseError"

SCSBID_BASE = "https://apis.data.go.kr/1230000/as/ScsbidInfoService"
# 업무구분 → 낙찰목록현황 오퍼레이션 (PPSSrch 없는 전수)
WINNER_OPERATIONS = {
    "용역": "getScsbidListSttusServc",
    "물품": "getScsbidListSttusThng",
    "공사": "getScsbidListSttusCnstwk",
    "외자": "getScsbidListSttusFrgcpt",
}
WINNER_PAGE_SIZE = 999  # 1000 을 주면 10건만 온다
WINNER_MAX_PAGES = 40
WINNER_MAX_DAYS = 93  # 3개월. 그 이상은 분 단위로 늘어난다
OPENING_DATE_DIV = 2  # 1=등록일시, 2=개찰일시


def format_datetime_for_api(value: Optional[str] = None, is_end: bool = False) -> str:
    """날짜/시간을 API 형식(YYYYMMDDHHMM)으로 변환. ``None`` 이면 오늘."""
    if not value:
        return dt.datetime.now().strftime("%Y%m%d2359" if is_end else "%Y%m%d0000")
    clean = value.replace("-", "").replace(":", "").replace(" ", "")
    if len(clean) == 8 and clean.isdigit():
        return clean + ("2359" if is_end else "0000")
    if len(clean) == 12 and clean.isdigit():
        return clean
    raise ValueError(f"잘못된 날짜/시간 형식: {value}")


class PpsNarajangteoAPIClient(BaseDataGoClient):
    """나라장터 공공데이터개방표준 API 클라이언트.

    응답 ``body.items`` 는 다른 data.go.kr 서비스와 달리 리스트로 바로 온다
    (``normalize_items`` 가 처리).
    """

    base_url = "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService"
    key_env_prefix = "PPS_NARAJANGTEO"
    default_params = {"type": "json"}

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """오류는 ``response`` 대신 ``nkoneps.com.response.ResponseError`` 로 온다 (2026-09-20 확인)."""
        error = data.get(ERROR_WRAPPER)
        if isinstance(error, Mapping):
            header = error.get("header") or {}
            raise DataGoAPIError(
                str(header.get("resultCode", "")), str(header.get("resultMsg", ""))
            )
        return super()._check_response(data)

    async def get_bid_announcements(
        self,
        bid_notice_begin_dt: str,
        bid_notice_end_dt: str,
        num_of_rows: int = 10,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """입찰공고정보 조회. 공고일시 범위는 최대 1개월 (YYYYMMDDHHMM)."""
        return await self.get(
            "getDataSetOpnStdBidPblancInfo",
            {
                "bidNtceBgnDt": bid_notice_begin_dt,
                "bidNtceEndDt": bid_notice_end_dt,
                "numOfRows": num_of_rows,
                "pageNo": page_no,
            },
        )

    async def get_successful_bids(
        self,
        business_div_code: str,
        opening_begin_dt: Optional[str] = None,
        opening_end_dt: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """낙찰정보 조회. 업무구분(1:물품, 2:외자, 3:공사, 5:용역), 개찰일시 범위는 하루(2일부터 코드 07)."""
        return await self.get(
            "getDataSetOpnStdScsbidInfo",
            {
                "bsnsDivCd": business_div_code,
                "opengBgnDt": opening_begin_dt,
                "opengEndDt": opening_end_dt,
                "numOfRows": num_of_rows,
                "pageNo": page_no,
            },
        )

    async def find_bid_winners(
        self,
        business_number: Optional[str] = None,
        company_name: Optional[str] = None,
        business_type: str = "용역",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """낙찰업체로 낙찰 건을 찾는다. API 가 업체 필터를 무시하므로 기간을 훑어 거른다."""
        bizno = re.sub(r"\D", "", business_number or "")
        name = (company_name or "").strip()
        if not bizno and not name:
            raise ValueError(
                "사업자번호(business_number) 또는 업체명(company_name) 중 하나는 필요합니다"
            )
        if business_number and len(bizno) != 10:
            raise ValueError(f"사업자번호는 숫자 10자리여야 합니다: {business_number!r}")

        operation = WINNER_OPERATIONS.get((business_type or "").strip())
        if operation is None:
            raise ValueError(
                f"업무구분은 {', '.join(WINNER_OPERATIONS)} 중 하나여야 합니다: {business_type!r}"
            )

        bgn, end = self._winner_range(start_date, end_date)
        scanned = 0
        hits: list[dict[str, Any]] = []
        for page_no in range(1, WINNER_MAX_PAGES + 1):
            body = await self._winner_page(operation, bgn, end, page_no)
            rows = normalize_items(body)
            scanned += len(rows)
            hits += [r for r in rows if _winner_matches(r, bizno, name)]
            total = int(body.get("totalCount") or 0)
            if len(rows) < WINNER_PAGE_SIZE or scanned >= total:
                break
        return {
            "items": [_winner_item(r) for r in hits],
            "total_count": len(hits),
            "scanned_count": scanned,
            "search_period": f"{bgn[:8]} ~ {end[:8]}",
        }

    async def _winner_page(
        self, operation: str, bgn: str, end: str, page_no: int
    ) -> dict[str, Any]:
        response = await self.http.get(
            f"{SCSBID_BASE}/{operation}",
            params=self._params(
                {
                    "inqryDiv": OPENING_DATE_DIV,
                    "inqryBgnDt": bgn,
                    "inqryEndDt": end,
                    "numOfRows": WINNER_PAGE_SIZE,
                    "pageNo": page_no,
                }
            ),
        )
        return self._handle(response)

    @staticmethod
    def _winner_range(start_date: Optional[str], end_date: Optional[str]) -> tuple[str, str]:
        """기본은 최근 1개월. 최대 3개월."""
        if not start_date and not end_date:
            today = dt.datetime.now()
            begin = today - dt.timedelta(days=30)
            return begin.strftime("%Y%m%d0000"), today.strftime("%Y%m%d2359")
        bgn = format_datetime_for_api(start_date or end_date or "", is_end=False)
        end = format_datetime_for_api(end_date or start_date or "", is_end=True)
        span = (
            dt.datetime.strptime(end[:8], "%Y%m%d") - dt.datetime.strptime(bgn[:8], "%Y%m%d")
        ).days
        if span > WINNER_MAX_DAYS:
            raise ValueError(
                f"낙찰업체 조회는 최대 3개월까지입니다: {bgn[:8]} ~ {end[:8]} ({span}일). "
                "기간을 나눠 호출하세요 (전체를 훑어 거르므로 기간이 길수록 느립니다)"
            )
        return bgn, end

    async def get_contracts(
        self,
        contract_begin_date: Optional[str] = None,
        contract_end_date: Optional[str] = None,
        institution_div_code: Optional[str] = None,
        institution_code: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """계약정보 조회. 계약체결일자(YYYYMMDD) 범위 최대 1개월."""
        return await self.get(
            "getDataSetOpnStdCntrctInfo",
            {
                "cntrctCnclsBgnDate": contract_begin_date,
                "cntrctCnclsEndDate": contract_end_date,
                "insttDivCd": institution_div_code,
                "insttCd": institution_code,
                "numOfRows": num_of_rows,
                "pageNo": page_no,
            },
        )


def _winner_matches(row: Mapping[str, Any], bizno: str, name: str) -> bool:
    """사업자번호는 정확히, 업체명은 부분 일치."""
    if bizno:
        return re.sub(r"\D", "", str(row.get("bidwinnrBizno") or "")) == bizno
    return name in str(row.get("bidwinnrNm") or "")


def _winner_item(row: Mapping[str, Any]) -> dict[str, Any]:
    """낙찰 한 건을 정규화한다."""

    def number(value: Any) -> Any:
        text = str(value or "").replace(",", "").strip()
        if not text:
            return None
        try:
            return int(text) if text.isdigit() else float(text)
        except ValueError:
            return None

    return {
        "company_name": (row.get("bidwinnrNm") or "").strip() or None,
        "business_number": (row.get("bidwinnrBizno") or "").strip() or None,
        "ceo_name": (row.get("bidwinnrCeoNm") or "").strip() or None,
        "address": (row.get("bidwinnrAdrs") or "").strip() or None,
        "bid_notice_no": (row.get("bidNtceNo") or "").strip() or None,
        "bid_notice_name": (row.get("bidNtceNm") or "").strip() or None,
        "winning_amount": number(row.get("sucsfbidAmt")),
        "winning_rate": number(row.get("sucsfbidRate")),
        "opening_date": (row.get("rlOpengDt") or "")[:10] or None,
        "final_award_date": (row.get("fnlSucsfDate") or "").strip() or None,
        "demand_institution": (row.get("dminsttNm") or "").strip() or None,
        "participant_count": number(row.get("prtcptCnum")),
    }
