"""API client for FSC Corporate Financial Information (금융위원회 기업 재무정보)."""

from decimal import Decimal, InvalidOperation
from typing import Any

from data_go_mcp.core import BaseDataGoClient, normalize_items

from .models import (
    BalanceSheetItem,
    BalanceSheetResponse,
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
