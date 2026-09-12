"""API client for FSC Corporate Financial Information (금융위원회 기업 재무정보)."""

from decimal import Decimal, InvalidOperation
from typing import Any

from data_go_mcp.core import BaseDataGoClient, normalize_items

from .models import (
    BalanceSheetItem,
    BalanceSheetResponse,
    CorpOutline,
    CorpSearchRequest,
    FinancialRequest,
    IncomeStatementItem,
    IncomeStatementResponse,
    SummaryFinancialResponse,
    SummaryFinancialStatement,
)


def parse_decimal(value: Any) -> Decimal | None:
    """API 금액 문자열("12,345" 등)을 Decimal로. 빈 값/파싱 불가는 ``None``."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError, TypeError):
        return None


class FSCFinancialAPIClient(BaseDataGoClient):
    """금융위원회 기업 재무정보 API 클라이언트 (JSON 응답 사용)."""

    base_url = "https://apis.data.go.kr/1160100/service/GetFinaStatInfoService_V2"
    key_env_prefix = "FSC_FINANCIAL_INFO"
    default_params = {"resultType": "json"}

    async def _fetch(
        self,
        endpoint: str,
        crno: str | None,
        biz_year: str | None,
        page_no: int,
        num_of_rows: int,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """요청 모델로 입력을 검증한 뒤 호출. (body, items) 반환."""
        request = FinancialRequest(
            crno=crno, biz_year=biz_year, page_no=page_no, num_of_rows=num_of_rows
        )
        body = await self.get(
            endpoint,
            {
                "pageNo": request.page_no,
                "numOfRows": request.num_of_rows,
                "crno": request.crno,
                "bizYear": request.biz_year,
            },
        )
        return body, normalize_items(body)

    @staticmethod
    def _meta(body: dict[str, Any]) -> dict[str, Any]:
        return {
            "result_code": "00",
            "result_msg": "NORMAL SERVICE.",
            "num_of_rows": int(body.get("numOfRows", 0)),
            "page_no": int(body.get("pageNo", 1)),
            "total_count": int(body.get("totalCount", 0)),
        }

    @staticmethod
    def _common(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "bas_dt": item.get("basDt"),
            "crno": item.get("crno"),
            "cur_cd": item.get("curCd"),
            "biz_year": item.get("bizYear"),
            "fncl_dcd": item.get("fnclDcd"),
            "fncl_dcd_nm": item.get("fnclDcdNm"),
        }

    @classmethod
    def _account(cls, item: dict[str, Any]) -> dict[str, Any]:
        return {
            **cls._common(item),
            "acit_id": item.get("acitId"),
            "acit_nm": item.get("acitNm"),
            "thqr_acit_amt": parse_decimal(item.get("thqrAcitAmt")),
            "crtm_acit_amt": parse_decimal(item.get("crtmAcitAmt")),
            "lsqt_acit_amt": parse_decimal(item.get("lsqtAcitAmt")),
            "pvtr_acit_amt": parse_decimal(item.get("pvtrAcitAmt")),
            "bpvtr_acit_amt": parse_decimal(item.get("bpvtrAcitAmt")),
        }

    async def get_summary_financial_statement(
        self,
        crno: str | None = None,
        biz_year: str | None = None,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> SummaryFinancialResponse:
        """요약재무제표 조회 (getSummFinaStat_V2)."""
        body, items = await self._fetch(
            "getSummFinaStat_V2", crno, biz_year, page_no, num_of_rows
        )
        statements = [
            SummaryFinancialStatement(
                **self._common(item),
                enp_sale_amt=parse_decimal(item.get("enpSaleAmt")),
                enp_bzop_pft=parse_decimal(item.get("enpBzopPft")),
                icls_pal_clc_amt=parse_decimal(item.get("iclsPalClcAmt")),
                enp_crtm_npf=parse_decimal(item.get("enpCrtmNpf")),
                enp_tast_amt=parse_decimal(item.get("enpTastAmt")),
                enp_tdbt_amt=parse_decimal(item.get("enpTdbtAmt")),
                enp_tcpt_amt=parse_decimal(item.get("enpTcptAmt")),
                enp_cptl_amt=parse_decimal(item.get("enpCptlAmt")),
                fncl_debt_rto=parse_decimal(item.get("fnclDebtRto")),
            )
            for item in items
        ]
        return SummaryFinancialResponse(**self._meta(body), items=statements)

    async def get_balance_sheet(
        self,
        crno: str | None = None,
        biz_year: str | None = None,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> BalanceSheetResponse:
        """재무상태표 조회 (getBs_V2)."""
        body, items = await self._fetch(
            "getBs_V2", crno, biz_year, page_no, num_of_rows
        )
        return BalanceSheetResponse(
            **self._meta(body),
            items=[BalanceSheetItem(**self._account(i)) for i in items],
        )

    async def get_income_statement(
        self,
        crno: str | None = None,
        biz_year: str | None = None,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> IncomeStatementResponse:
        """손익계산서 조회 (getIncoStat_V2)."""
        body, items = await self._fetch(
            "getIncoStat_V2", crno, biz_year, page_no, num_of_rows
        )
        return IncomeStatementResponse(
            **self._meta(body),
            items=[IncomeStatementItem(**self._account(i)) for i in items],
        )


def latest_per_crno(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """같은 crno 의 스냅샷 중 ``lastOpegDt`` 가 가장 늦은 것만 남긴다 (첫 등장 순서 유지)."""
    latest: dict[str, dict[str, Any]] = {}
    for item in items:
        crno = item.get("crno", "")
        if crno not in latest or item.get("lastOpegDt", "") > latest[crno].get(
            "lastOpegDt", ""
        ):
            latest[crno] = item
    return list(latest.values())


class CorpBasicInfoAPIClient(BaseDataGoClient):
    """금융위원회 기업기본정보 API (GetCorpBasicInfoService_V2).

    법인명·사업자등록번호 → 법인등록번호(crno) 매핑과 기업 개요에 쓴다. 응답은 유효기간별
    스냅샷이라 같은 법인이 여러 번 오므로 최신 것만 돌려준다.
    """

    base_url = "https://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2"
    key_env_prefix = "FSC_FINANCIAL_INFO"
    default_params = {"resultType": "json"}

    async def _outline(
        self, request: CorpSearchRequest
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        body = await self.get(
            "getCorpOutline_V2",
            {
                "pageNo": request.page_no,
                "numOfRows": request.num_of_rows,
                "corpNm": request.corp_nm,
                "bzno": request.bzno,
                "crno": request.crno,
            },
        )
        return body, normalize_items(body)

    async def search_corporations(
        self,
        corp_name: str | None = None,
        bzno: str | None = None,
        page_no: int = 1,
        num_of_rows: int = 100,
    ) -> dict[str, Any]:
        """법인명(부분 일치) 또는 사업자등록번호로 법인을 찾는다. ``total_count`` 는 스냅샷 건수."""
        request = CorpSearchRequest(
            corp_nm=corp_name, bzno=bzno, page_no=page_no, num_of_rows=num_of_rows
        )
        if request.corp_nm is None and request.bzno is None:
            raise ValueError(
                "법인명(corp_name) 또는 사업자등록번호(bzno) 중 하나는 필요합니다"
            )
        body, items = await self._outline(request)
        return {
            "items": [
                CorpOutline.from_api(i).model_dump() for i in latest_per_crno(items)
            ],
            "page_no": request.page_no,
            "num_of_rows": request.num_of_rows,
            "total_count": int(body.get("totalCount", 0)),
        }

    MAX_OUTLINE_PAGES = 5

    async def get_corp_outline(self, crno: str) -> dict[str, Any] | None:
        """법인등록번호로 최신 기업 개요. 없으면 ``None``.

        스냅샷이 한 페이지(100건)를 넘으면 뒷 페이지도 읽어 최신을 고른다 (최대 5페이지).
        """
        request = CorpSearchRequest(crno=crno, num_of_rows=100)
        body, items = await self._outline(request)
        total = int(body.get("totalCount", 0))
        page = 1
        while len(items) < total and page < self.MAX_OUTLINE_PAGES:
            page += 1
            _, more = await self._outline(request.model_copy(update={"page_no": page}))
            items.extend(more)
            if len(more) < request.num_of_rows:  # 짧은 페이지 = 마지막
                break
        latest = latest_per_crno(items)
        return CorpOutline.from_api(latest[0]).model_dump() if latest else None
