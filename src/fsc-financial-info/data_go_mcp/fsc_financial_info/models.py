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


def _digits(v: str | None, label: str, length: int) -> str | None:
    if v is None:
        return None
    v = v.replace("-", "").strip()
    if not v.isdigit() or len(v) != length:
        raise ValueError(f"{label}는 {length}자리 숫자여야 합니다")
    return v


class CorpSearchRequest(BaseRequest):
    """기업기본정보(getCorpOutline_V2) 요청 모델. corp_nm 은 부분 일치, bzno/crno 는 정확히 일치."""

    num_of_rows: int = Field(default=100, ge=1, le=100, description="한 페이지 결과 수")
    corp_nm: str | None = Field(default=None, description="법인명 (부분 일치)")
    bzno: str | None = Field(default=None, description="사업자등록번호 (10자리)")
    crno: str | None = Field(default=None, description="법인등록번호 (13자리)")

    @field_validator("corp_nm")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        return v or None

    @field_validator("bzno")
    @classmethod
    def _validate_bzno(cls, v: str | None) -> str | None:
        return _digits(v, "사업자등록번호", 10)

    @field_validator("crno")
    @classmethod
    def _validate_crno(cls, v: str | None) -> str | None:
        return _digits(v, "법인등록번호", 13)


def _int_or_none(v: str | int | None) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(str(v).replace(",", ""))
    except ValueError:
        return None


class CorpOutline(BaseModel):
    """기업 개요 한 스냅샷. 빈 문자열은 None 으로."""

    crno: str = Field(description="법인등록번호")
    corp_nm: str = Field(description="법인명")
    corp_ensn_nm: str | None = Field(default=None, description="법인 영문명")
    enp_pban_cmpy_nm: str | None = Field(default=None, description="기업 공시회사명")
    enp_rpr_fnm: str | None = Field(default=None, description="대표자명")
    market: str | None = Field(
        default=None, description="상장시장 (유가/코스닥/코넥스/기타)"
    )
    bzno: str | None = Field(default=None, description="사업자등록번호")
    enp_bsadr: str | None = Field(default=None, description="기본주소")
    enp_dtadr: str | None = Field(default=None, description="상세주소")
    enp_hmpg_url: str | None = Field(default=None, description="홈페이지")
    enp_tlno: str | None = Field(default=None, description="전화번호")
    enp_estb_dt: str | None = Field(default=None, description="설립일자 (YYYYMMDD)")
    enp_stac_mm: str | None = Field(default=None, description="결산월")
    enp_xchg_lstg_dt: str | None = Field(default=None, description="유가증권 상장일")
    enp_kosdaq_lstg_dt: str | None = Field(default=None, description="코스닥 상장일")
    enp_empe_cnt: int | None = Field(default=None, description="종업원 수")
    empe_avg_cnwk_term_ctt: str | None = Field(
        default=None, description="평균 근속연수"
    )
    enp_pn1_avg_slry_amt: int | None = Field(
        default=None, description="1인 평균 급여액 (원)"
    )
    actn_audpn_nm: str | None = Field(default=None, description="회계감사인")
    audt_rpt_opnn_ctt: str | None = Field(default=None, description="감사의견")
    enp_main_biz_nm: str | None = Field(default=None, description="주요사업")
    fss_corp_unq_no: str | None = Field(
        default=None, description="금감원 고유번호 (DART corp_code)"
    )
    snapshot_dt: str = Field(description="이 정보의 최종 유효일 (lastOpegDt)")

    @classmethod
    def from_api(cls, raw: dict) -> "CorpOutline":
        """API camelCase 항목 → 모델. 빈 문자열은 None."""
        g = lambda k: raw.get(k) or None  # noqa: E731
        return cls(
            crno=raw["crno"],
            corp_nm=raw.get("corpNm") or "",
            corp_ensn_nm=g("corpEnsnNm"),
            enp_pban_cmpy_nm=g("enpPbanCmpyNm"),
            enp_rpr_fnm=g("enpRprFnm"),
            market=g("corpRegMrktDcdNm"),
            bzno=g("bzno"),
            enp_bsadr=g("enpBsadr"),
            enp_dtadr=g("enpDtadr"),
            enp_hmpg_url=g("enpHmpgUrl"),
            enp_tlno=g("enpTlno"),
            enp_estb_dt=g("enpEstbDt"),
            enp_stac_mm=g("enpStacMm"),
            enp_xchg_lstg_dt=g("enpXchgLstgDt"),
            enp_kosdaq_lstg_dt=g("enpKosdaqLstgDt"),
            enp_empe_cnt=_int_or_none(raw.get("enpEmpeCnt")),
            empe_avg_cnwk_term_ctt=g("empeAvgCnwkTermCtt"),
            enp_pn1_avg_slry_amt=_int_or_none(raw.get("enpPn1AvgSlryAmt")),
            actn_audpn_nm=g("actnAudpnNm"),
            audt_rpt_opnn_ctt=g("audtRptOpnnCtt"),
            enp_main_biz_nm=g("enpMainBizNm"),
            fss_corp_unq_no=g("fssCorpUnqNo"),
            snapshot_dt=raw.get("lastOpegDt") or "",
        )
