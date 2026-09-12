"""
Data models for FSC Corporate Financial Information API.
금융위원회 기업 재무정보 API 데이터 모델.
"""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, PlainSerializer, field_validator


class BaseRequest(BaseModel):
    """Base request model with common pagination parameters."""

    num_of_rows: int = Field(default=10, ge=1, le=100, description="한 페이지 결과 수")
    page_no: int = Field(default=1, ge=1, description="페이지 번호")
    result_type: Literal["json", "xml"] = Field(default="json", description="결과형식")


class FinancialRequest(BaseRequest):
    """Request model for financial statements queries."""

    crno: str | None = Field(default=None, description="법인등록번호 (13자리)")
    biz_year: str | None = Field(default=None, description="사업연도 (4자리)")

    @field_validator("crno")
    @classmethod
    def validate_crno(cls, v: str | None) -> str | None:
        """Validate corporate registration number format."""
        if v is None:
            return v
        # Remove any hyphens
        v = v.replace("-", "").strip()
        if not v.isdigit() or len(v) != 13:
            raise ValueError("법인등록번호는 13자리 숫자여야 합니다")
        return v

    @field_validator("biz_year")
    @classmethod
    def validate_year(cls, v: str | None) -> str | None:
        """Validate business year format."""
        if v is None:
            return v
        v = str(v).strip()
        if not v.isdigit() or len(v) != 4:
            raise ValueError("사업연도는 4자리 숫자여야 합니다 (예: 2023)")
        year = int(v)
        if year < 1900 or year > 2100:
            raise ValueError("유효한 연도를 입력해주세요")
        return v


# JSON 직렬화 시 Decimal 을 숫자로. 필드 단위라 스키마의 타입 정보는 그대로 남는다.
JsonDecimal = Annotated[
    Decimal, PlainSerializer(float, return_type=float, when_used="json")
]


class SummaryFinancialStatement(BaseModel):
    """Summary financial statement model (요약재무제표)."""

    bas_dt: str | None = Field(default=None, description="기준일자")
    crno: str = Field(description="법인등록번호")
    cur_cd: str | None = Field(default=None, description="통화 코드")
    biz_year: str = Field(description="사업연도")
    fncl_dcd: str | None = Field(default=None, description="재무제표구분코드")
    fncl_dcd_nm: str | None = Field(default=None, description="재무제표구분코드명")

    # Financial metrics (amounts)
    enp_sale_amt: JsonDecimal | None = Field(default=None, description="기업매출금액")
    enp_bzop_pft: JsonDecimal | None = Field(default=None, description="기업영업이익")
    icls_pal_clc_amt: JsonDecimal | None = Field(
        default=None, description="포괄손익계산금액"
    )
    enp_crtm_npf: JsonDecimal | None = Field(default=None, description="기업당기순이익")
    enp_tast_amt: JsonDecimal | None = Field(default=None, description="기업총자산금액")
    enp_tdbt_amt: JsonDecimal | None = Field(default=None, description="기업총부채금액")
    enp_tcpt_amt: JsonDecimal | None = Field(default=None, description="기업총자본금액")
    enp_cptl_amt: JsonDecimal | None = Field(default=None, description="기업자본금액")
    fncl_debt_rto: JsonDecimal | None = Field(
        default=None, description="재무제표부채비율"
    )


class BalanceSheetItem(BaseModel):
    """Balance sheet item model (재무상태표 항목)."""

    bas_dt: str | None = Field(default=None, description="기준일자")
    crno: str = Field(description="법인등록번호")
    cur_cd: str | None = Field(default=None, description="통화 코드")
    biz_year: str = Field(description="사업연도")
    fncl_dcd: str | None = Field(default=None, description="재무제표구분코드")
    fncl_dcd_nm: str | None = Field(default=None, description="재무제표구분코드명")

    # Account information
    acit_id: str | None = Field(default=None, description="계정과목ID")
    acit_nm: str | None = Field(default=None, description="계정과목명")

    # Period amounts
    thqr_acit_amt: JsonDecimal | None = Field(
        default=None, description="당분기계정과목금액"
    )
    crtm_acit_amt: JsonDecimal | None = Field(
        default=None, description="당기계정과목금액"
    )
    lsqt_acit_amt: JsonDecimal | None = Field(
        default=None, description="전분기계정과목금액"
    )
    pvtr_acit_amt: JsonDecimal | None = Field(
        default=None, description="전기계정과목금액"
    )
    bpvtr_acit_amt: JsonDecimal | None = Field(
        default=None, description="전전기계정과목금액"
    )


class IncomeStatementItem(BaseModel):
    """Income statement item model (손익계산서 항목)."""

    bas_dt: str | None = Field(default=None, description="기준일자")
    crno: str = Field(description="법인등록번호")
    cur_cd: str | None = Field(default=None, description="통화 코드")
    biz_year: str = Field(description="사업연도")
    fncl_dcd: str | None = Field(default=None, description="재무제표구분코드")
    fncl_dcd_nm: str | None = Field(default=None, description="재무제표구분코드명")

    # Account information
    acit_id: str | None = Field(default=None, description="계정과목ID")
    acit_nm: str | None = Field(default=None, description="계정과목명")

    # Period amounts
    thqr_acit_amt: JsonDecimal | None = Field(
        default=None, description="당분기계정과목금액"
    )
    crtm_acit_amt: JsonDecimal | None = Field(
        default=None, description="당기계정과목금액"
    )
    lsqt_acit_amt: JsonDecimal | None = Field(
        default=None, description="전분기계정과목금액"
    )
    pvtr_acit_amt: JsonDecimal | None = Field(
        default=None, description="전기계정과목금액"
    )
    bpvtr_acit_amt: JsonDecimal | None = Field(
        default=None, description="전전기계정과목금액"
    )


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    result_code: str = Field(description="결과코드")
    result_msg: str = Field(description="결과메시지")
    num_of_rows: int = Field(description="한 페이지 결과 수")
    page_no: int = Field(description="페이지 번호")
    total_count: int = Field(description="전체 결과 수")

    def is_success(self) -> bool:
        """Check if the API response is successful."""
        return self.result_code == "00"


class SummaryFinancialResponse(APIResponse):
    """Response model for summary financial statements."""

    items: list[SummaryFinancialStatement] = Field(
        default_factory=list, description="요약재무제표 목록"
    )


class BalanceSheetResponse(APIResponse):
    """Response model for balance sheet."""

    items: list[BalanceSheetItem] = Field(
        default_factory=list, description="재무상태표 항목 목록"
    )


class IncomeStatementResponse(APIResponse):
    """Response model for income statement."""

    items: list[IncomeStatementItem] = Field(
        default_factory=list, description="손익계산서 항목 목록"
    )
