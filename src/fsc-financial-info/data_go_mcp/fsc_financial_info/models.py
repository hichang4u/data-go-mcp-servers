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


def _positive_int_or_none(v: str | int | None) -> int | None:
    """공시하지 않는 법인은 "0" 으로 오므로 0 도 None 으로 본다."""
    if v is None or v == "":
        return None
    try:
        n = int(str(v).replace(",", ""))
    except ValueError:
        return None
    return n if n > 0 else None


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
    enp_empe_cnt: int | None = Field(
        default=None, description="종업원 수 (미공시면 null)"
    )
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
            enp_empe_cnt=_positive_int_or_none(raw.get("enpEmpeCnt")),
            empe_avg_cnwk_term_ctt=g("empeAvgCnwkTermCtt"),
            enp_pn1_avg_slry_amt=_positive_int_or_none(raw.get("enpPn1AvgSlryAmt")),
            actn_audpn_nm=g("actnAudpnNm"),
            audt_rpt_opnn_ctt=g("audtRptOpnnCtt"),
            enp_main_biz_nm=g("enpMainBizNm"),
            fss_corp_unq_no=g("fssCorpUnqNo"),
            snapshot_dt=raw.get("lastOpegDt") or "",
        )


def _yyyymmdd(v: str | None, label: str) -> str | None:
    if v is None:
        return None
    v = v.replace("-", "").strip()
    if not v.isdigit() or len(v) != 8:
        raise ValueError(f"{label}는 YYYYMMDD 형식이어야 합니다")
    return v


class StockPriceRequest(BaseRequest):
    """주식시세(getStockPriceInfo_V2) 요청 모델."""

    itms_nm: str | None = Field(default=None, description="종목명 (정확히 일치)")
    like_itms_nm: str | None = Field(default=None, description="종목명 (부분 일치)")
    srtn_cd: str | None = Field(default=None, description="단축코드 (6자리)")
    isin_cd: str | None = Field(default=None, description="ISIN 코드 (12자리)")
    bas_dt: str | None = Field(default=None, description="기준일자 (YYYYMMDD)")
    begin_bas_dt: str | None = Field(default=None, description="기준일자 시작 (이상)")
    end_bas_dt: str | None = Field(default=None, description="기준일자 끝 (이하)")

    @field_validator("itms_nm", "like_itms_nm", "isin_cd")
    @classmethod
    def _strip(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        return v or None

    @field_validator("srtn_cd")
    @classmethod
    def _validate_srtn_cd(cls, v: str | None) -> str | None:
        return _digits(v, "단축코드", 6)

    @field_validator("bas_dt", "begin_bas_dt", "end_bas_dt")
    @classmethod
    def _validate_dates(cls, v: str | None) -> str | None:
        return _yyyymmdd(v, "기준일자")


def _int_or_none(v: str | int | None) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(str(v).replace(",", ""))
    except ValueError:
        return None


def _float_or_none(v: str | float | None) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


class StockPrice(BaseModel):
    """일별 주식 시세 한 건."""

    bas_dt: str = Field(description="기준일자 (YYYYMMDD)")
    srtn_cd: str = Field(description="단축코드 (6자리)")
    isin_cd: str | None = Field(default=None, description="ISIN 코드")
    itms_nm: str = Field(description="종목명")
    mrkt_ctg: str | None = Field(
        default=None, description="시장구분 (KOSPI/KOSDAQ/KONEX)"
    )
    clpr: int | None = Field(default=None, description="종가 (원)")
    vs: int | None = Field(default=None, description="전일 대비 (원)")
    flt_rt: float | None = Field(default=None, description="등락률 (%)")
    mkp: int | None = Field(default=None, description="시가")
    hipr: int | None = Field(default=None, description="고가")
    lopr: int | None = Field(default=None, description="저가")
    trqu: int | None = Field(default=None, description="거래량 (주)")
    tr_prc: int | None = Field(default=None, description="거래대금 (원)")
    lstg_st_cnt: int | None = Field(default=None, description="상장주식수")
    mrkt_tot_amt: int | None = Field(default=None, description="시가총액 (원)")

    @classmethod
    def from_api(cls, raw: dict) -> "StockPrice":
        """API camelCase 항목 → 모델."""
        return cls(
            bas_dt=raw.get("basDt") or "",
            srtn_cd=raw.get("srtnCd") or "",
            isin_cd=raw.get("isinCd") or None,
            itms_nm=raw.get("itmsNm") or "",
            mrkt_ctg=raw.get("mrktCtg") or None,
            clpr=_int_or_none(raw.get("clpr")),
            vs=_int_or_none(raw.get("vs")),
            flt_rt=_float_or_none(raw.get("fltRt")),
            mkp=_int_or_none(raw.get("mkp")),
            hipr=_int_or_none(raw.get("hipr")),
            lopr=_int_or_none(raw.get("lopr")),
            trqu=_int_or_none(raw.get("trqu")),
            tr_prc=_int_or_none(raw.get("trPrc")),
            lstg_st_cnt=_int_or_none(raw.get("lstgStCnt")),
            mrkt_tot_amt=_int_or_none(raw.get("mrktTotAmt")),
        )
