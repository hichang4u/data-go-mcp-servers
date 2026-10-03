"""API client for 나라장터 — 공공데이터개방표준서비스, 낙찰정보서비스, 사용자정보서비스.

낙찰업체 조회(``find_bid_winners``)만 낙찰정보서비스(``as/ScsbidInfoService``)를 쓴다.
2026-09-30 실호출로 확인한 것:

- 개방표준서비스의 낙찰정보에는 **업체 정보가 아예 없다**. 낙찰업체 사업자번호·상호는
  낙찰정보서비스의 ``getScsbidListSttus*`` 응답에만 있다
- 그런데 ``bidwinnrBizno``/``bidwinnrNm`` 을 요청 파라미터로 주면 **무시된다** (전체가 온다)
  → 기간을 999건씩 훑어 클라이언트에서 거른다
- ``PPSSrch`` 가 붙은 오퍼레이션은 부분집합이다 (같은 날 53건 vs 357건) → 전수 쪽을 쓴다
- ``inqryDiv=1`` 은 등록일시, ``inqryDiv=2`` 가 **개찰일시** 기준이다
- **한 요청의 기간 한도는 1개월**이다 (넘기면 코드 07). 그래서 더 긴 기간은 달 단위로 쪼개
  호출한다. 용역 1개월 전수가 4~8페이지 15~35초, 3개월이 19요청 약 70초

업체 조회(``get_procurement_company``, ``check_procurement_sanctions``)는 사용자정보서비스
(``ao/UsrInfoService02``)를 쓴다. 이쪽은 낙찰정보와 달리 **사업자번호 필터가 실제로 동작한다**
(2026-10-03 확인). 대신 오퍼레이션마다 '사업자등록번호 기준검색'의 ``inqryDiv`` 코드가 다르다.
"""

import asyncio
import datetime as dt
import re
from typing import Any, Awaitable, Mapping, NamedTuple, Optional

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
WINNER_TIMEOUT = 90.0  # 한 페이지가 999건이라 기본 30초로는 모자랄 때가 있다

CORP_BASE = "https://apis.data.go.kr/1230000/ao/UsrInfoService02"
# 오퍼레이션 → (경로, 사업자번호 기준검색의 inqryDiv). **코드가 제각각이다** — 기본정보만 3,
# 나머지는 1. 하나로 묶으면 조회구분이 달라져 조용히 다른 결과가 온다 (2026-10-03 실호출 확인).
CORP_OPERATIONS = {
    "basic": ("getPrcrmntCorpBasicInfo02", "3"),
    "industry": ("getPrcrmntCorpIndstrytyInfo02", "1"),
    "supply": ("getPrcrmntCorpSplyPrdctInfo02", "1"),
    "sanction": ("getUnptRsttCorpInfo02", "1"),
}
CORP_PAGE_SIZE = 100


def _now() -> "dt.datetime":
    """현재 시각. 테스트가 이 함수만 갈아끼운다."""
    return dt.datetime.now()


def format_datetime_for_api(value: Optional[str] = None, is_end: bool = False) -> str:
    """날짜/시간을 API 형식(YYYYMMDDHHMM)으로 변환. ``None`` 이면 오늘."""
    if not value:
        return _now().strftime("%Y%m%d2359" if is_end else "%Y%m%d0000")
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
        complete = True
        hits: list[dict[str, Any]] = []
        for window_bgn, window_end in _monthly_windows(bgn, end):
            window_scanned = 0
            window_total = 0
            for page_no in range(1, WINNER_MAX_PAGES + 1):
                body = await self._winner_page(operation, window_bgn, window_end, page_no)
                rows = normalize_items(body)
                window_total = int(body.get("totalCount") or 0)
                window_scanned += len(rows)
                hits += [r for r in rows if _winner_matches(r, bizno, name)]
                if not rows or window_scanned >= window_total:
                    break
            if window_scanned < window_total:  # 페이지 상한에 걸렸거나 응답이 덜 왔다
                complete = False
            scanned += window_scanned
        return {
            "items": [_winner_item(r) for r in hits],
            "total_count": len(hits),
            "scanned_count": scanned,
            "complete": complete,
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
            today = _now()
            begin = today - dt.timedelta(days=30)
            return begin.strftime("%Y%m%d0000"), today.strftime("%Y%m%d2359")
        bgn = format_datetime_for_api(start_date or end_date or "", is_end=False)
        end = format_datetime_for_api(end_date or start_date or "", is_end=True)
        span = (
            dt.datetime.strptime(end[:8], "%Y%m%d") - dt.datetime.strptime(bgn[:8], "%Y%m%d")
        ).days + 1  # 다른 pps 툴과 같은 포함 기준
        if span < 1:
            raise ValueError(f"시작일이 종료일보다 늦습니다: {bgn[:8]} ~ {end[:8]}")
        if span > WINNER_MAX_DAYS:
            raise ValueError(
                f"낙찰업체 조회는 최대 3개월까지입니다: {bgn[:8]} ~ {end[:8]} ({span}일). "
                "기간을 나눠 호출하세요 (전체를 훑어 거르므로 기간이 길수록 느립니다)"
            )
        return bgn, end

    async def get_procurement_company(self, business_number: str) -> dict[str, Any]:
        """조달 등록업체 정보. 기본정보·등록업종·공급물품을 한 번에 모은다."""
        bizno = normalize_business_number(business_number)
        basic, industry, supply = await _gather_all(
            self._corp_rows("basic", bizno),
            self._corp_rows("industry", bizno),
            self._corp_rows("supply", bizno),
        )
        company = _corp_company(basic.rows[0]) if basic.rows else None
        industries = [_corp_industry(r) for r in industry.rows]
        products = [_corp_product(r) for r in supply.rows]
        return {
            "company": company,
            "registered": company is not None,
            "industries": industries,
            "products": products,
            # 한 번에 CORP_PAGE_SIZE 건까지만 받는다. 총계를 함께 줘야 잘렸는지 알 수 있다
            "industry_count": industry.total,
            "product_count": supply.total,
            "complete": len(industries) >= industry.total and len(products) >= supply.total,
        }

    async def check_procurement_sanctions(self, business_number: str) -> dict[str, Any]:
        """부정당업자 제재 이력. 지금 제재 중인지도 함께 돌려준다."""
        bizno = normalize_business_number(business_number)
        page = await self._corp_rows("sanction", bizno)
        items = [_corp_sanction(r) for r in page.rows]
        return {
            "items": items,
            "total_count": page.total,  # len(items) 는 100 을 못 넘는다
            "complete": len(items) >= page.total,
            "restricted_now": any(i["in_effect"] for i in items),
        }

    async def _corp_rows(self, facet: str, bizno: str) -> "CorpPage":
        """사용자정보서비스 한 오퍼레이션을 호출한다. 총계도 함께 돌려준다."""
        operation, inqry_div = CORP_OPERATIONS[facet]
        response = await self.http.get(
            f"{CORP_BASE}/{operation}",
            params=self._params(
                {
                    "inqryDiv": inqry_div,
                    "bizno": bizno,
                    "numOfRows": CORP_PAGE_SIZE,
                    "pageNo": 1,
                }
            ),
        )
        body = self._handle(response)
        return CorpPage(normalize_items(body), int(body.get("totalCount") or 0))

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


def _monthly_windows(bgn: str, end: str) -> list[tuple[str, str]]:
    """``YYYYMMDDHHMM`` 범위를 달 단위 창으로 쪼갠다. API 가 한 요청에 1개월까지만 받는다."""
    start = dt.datetime.strptime(bgn[:8], "%Y%m%d").date()
    last = dt.datetime.strptime(end[:8], "%Y%m%d").date()
    windows: list[tuple[str, str]] = []
    while start <= last:
        if start.month == 12:
            month_end = start.replace(day=31)
        else:
            month_end = start.replace(month=start.month + 1, day=1) - dt.timedelta(days=1)
        stop = min(month_end, last)
        windows.append((start.strftime("%Y%m%d0000"), stop.strftime("%Y%m%d2359")))
        start = stop + dt.timedelta(days=1)
    return windows


class CorpPage(NamedTuple):
    """한 오퍼레이션의 결과 한 페이지와 API 가 말하는 총계."""

    rows: list[dict[str, Any]]
    total: int


async def _gather_all(*aws: "Awaitable[CorpPage]") -> list[CorpPage]:
    """Gather 하되 실패해도 나머지를 버려두지 않는다.

    ``asyncio.gather`` 는 첫 실패를 바로 올리고 남은 태스크를 취소하지 않는다. 그 뒤
    ``async with`` 가 커넥션 풀을 닫으면 남은 태스크가 닫힌 풀에서 실패하고, 아무도
    기다리지 않아 ``Task exception was never retrieved`` 가 stderr 에 남는다.
    """
    results = await asyncio.gather(*aws, return_exceptions=True)
    for result in results:
        if isinstance(result, BaseException):
            raise result
    return [r for r in results if isinstance(r, CorpPage)]


def normalize_business_number(value: str) -> str:
    """``"111-81-26895"`` → ``"1118126895"``. 틀린 값은 0건이 아니라 오류로 돌려준다."""
    bizno = re.sub(r"\D", "", value or "")
    if len(bizno) != 10:
        raise ValueError(f"사업자번호는 숫자 10자리여야 합니다: {value!r}")
    return bizno


def _corp_text(value: Any) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _corp_date(value: Any) -> Optional[str]:
    """``"1996-08-01 00:00:00"`` → ``"1996-08-01"``."""
    text = _corp_text(value)
    return text.split(" ")[0] if text else None


def _corp_int(value: Any) -> Optional[int]:
    text = str(value or "").replace(",", "").strip()
    return int(text) if text.isdigit() else None


def _corp_yn(value: Any) -> bool:
    return str(value or "").strip().upper() == "Y"


def _corp_company(row: Mapping[str, Any]) -> dict[str, Any]:
    """업체 기본정보 한 건."""
    address = " ".join(
        part for part in (_corp_text(row.get("adrs")), _corp_text(row.get("dtlAdrs"))) if part
    )
    types = _corp_text(row.get("corpBsnsDivNm"))
    return {
        "business_number": _corp_text(row.get("bizno")),
        "name": _corp_text(row.get("corpNm")),
        "english_name": _corp_text(row.get("engCorpNm")),
        "ceo": _corp_text(row.get("ceoNm")),
        "opened_on": _corp_date(row.get("opbizDt")),
        "region": _corp_text(row.get("rgnNm")),
        "address": address or None,
        "postal_code": _corp_text(row.get("zip")),
        "phone": _corp_text(row.get("telNo")),
        "fax": _corp_text(row.get("faxNo")),
        "homepage": _corp_text(row.get("hmpgAdrs")),
        "employees": _corp_int(row.get("emplyeNum")),
        "supply_type": _corp_text(row.get("mnfctDivNm")),
        "business_types": [t.strip() for t in types.split(",")] if types else [],
        "head_office": _corp_text(row.get("hdoffceDivNm")),
        "registered_on": _corp_date(row.get("rgstDt")),
        "changed_on": _corp_date(row.get("chgDt")),
    }


def _corp_industry(row: Mapping[str, Any]) -> dict[str, Any]:
    """등록 업종 한 건."""
    return {
        "name": _corp_text(row.get("indstrytyNm")),
        "code": _corp_text(row.get("indstrytyCd")),
        "status": _corp_text(row.get("indstrytyStatsNm")),
        "representative": _corp_yn(row.get("rprsntIndstrytyYn")),
        "registered_on": _corp_date(row.get("rgstDt")),
        "valid_until": _corp_date(row.get("vldPrdExprtDt")),
    }


def _corp_product(row: Mapping[str, Any]) -> dict[str, Any]:
    """공급물품 한 건."""
    return {
        "name": _corp_text(row.get("dtilPrdctClsfcNoNm")),
        "classification_code": _corp_text(row.get("dtilPrdctClsfcNo")),
        "representative": _corp_yn(row.get("rprsntPrdctClsfcNoNmYn")),
        "manufactured": _corp_yn(row.get("mnfctYn")),
        "registered_on": _corp_date(row.get("rgstDt")),
    }


def _corp_sanction(row: Mapping[str, Any]) -> dict[str, Any]:
    """부정당업자 제재 한 건. 제재 기간이 오늘을 품고 있으면 진행 중이다."""
    begins, ends = _corp_date(row.get("rsttBgnDate")), _corp_date(row.get("rsttEndDate"))
    return {
        "company_name": _corp_text(row.get("corpNm")),
        "business_number": _corp_text(row.get("bizno")),
        "institution": _corp_text(row.get("insttNm")),
        "begins_on": begins,
        "ends_on": ends,
        "in_effect": _corp_in_effect(begins, ends),
        "months": _corp_int(row.get("rsttPrdMonthNum")),
        "days": _corp_int(row.get("rsttPrdDayNum")),
        "status": _corp_text(row.get("rsttProgrsNm")),
        "law": _corp_text(row.get("lawordNm")),
        "clause": _corp_text(row.get("lawordArtclClause")),
        "reason": _corp_text(row.get("lawordArtclClauseCdNm")),
        "short_reason": _corp_text(row.get("enfcPrvNm")),
        "document": _corp_text(row.get("unptRsttDocNm")),
        "notified_on": _corp_text(row.get("ntfcnDt")),
    }


def _corp_in_effect(begins: Optional[str], ends: Optional[str]) -> bool:
    """오늘이 제재 기간 안인가."""
    today = dt.date.today().isoformat()
    if begins and begins > today:
        return False
    return bool(ends) and ends >= today


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

    def text(value: Any) -> Optional[str]:
        """숫자로 오는 필드가 있어 문자열로 맞춘다 (한 행이 스캔 전체를 날리지 않게)."""
        return str(value if value is not None else "").strip() or None

    return {
        "company_name": text(row.get("bidwinnrNm")),
        "business_number": text(row.get("bidwinnrBizno")),
        "ceo_name": text(row.get("bidwinnrCeoNm")),
        "address": text(row.get("bidwinnrAdrs")),
        "bid_notice_no": text(row.get("bidNtceNo")),
        "bid_notice_name": text(row.get("bidNtceNm")),
        "winning_amount": number(row.get("sucsfbidAmt")),
        "winning_rate": number(row.get("sucsfbidRate")),
        "opening_date": (text(row.get("rlOpengDt")) or "")[:10] or None,
        "final_award_date": text(row.get("fnlSucsfDate")),
        "demand_institution": text(row.get("dminsttNm")),
        "participant_count": number(row.get("prtcptCnum")),
    }
