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


# ── 지수시세 (GetMarketIndexInfoService_V2) ─────────────────────────────────────

INDEX_TYPES = {"주가": "getStockMarketIndex_V2", "채권": "getBondMarketIndex_V2"}
PRODUCT_TYPES = {"ETF": "getETFPriceInfo_V2", "ETN": "getETNPriceInfo_V2"}


class MarketIndexRequest(BaseRequest):
    """지수시세 요청 모델. 건수·페이지 한도는 BaseRequest 와 같다 (1~100)."""

    index_name: str | None = Field(default=None, description="지수명 (정확히 일치)")
    like_index_name: str | None = Field(default=None, description="지수명 (부분 일치)")
    bas_dt: str | None = Field(default=None, description="기준일자 (YYYYMMDD)")
    begin_bas_dt: str | None = Field(default=None, description="기준일자 시작 (이상)")
    end_bas_dt: str | None = Field(default=None, description="기준일자 끝 (이하)")

    @field_validator("index_name", "like_index_name")
    @classmethod
    def _strip_index(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        return v or None

    @field_validator("bas_dt")
    @classmethod
    def _validate_bas_dt(cls, v: str | None) -> str | None:
        return _yyyymmdd(v, "기준일자(bas_dt)")

    @field_validator("begin_bas_dt")
    @classmethod
    def _validate_begin(cls, v: str | None) -> str | None:
        return _yyyymmdd(v, "기준일자 시작(begin_bas_dt)")

    @field_validator("end_bas_dt")
    @classmethod
    def _validate_end(cls, v: str | None) -> str | None:
        return _yyyymmdd(v, "기준일자 끝(end_bas_dt)")


class ProductPriceRequest(MarketIndexRequest):
    """증권상품시세(ETF·ETN) 요청 모델. 단축코드가 영숫자라 자리수 검증을 하지 않는다."""

    item_name: str | None = Field(default=None, description="종목명 (정확히 일치)")
    like_item_name: str | None = Field(default=None, description="종목명 (부분 일치)")
    short_code: str | None = Field(default=None, description="단축코드 (영숫자 6자리)")
    isin_cd: str | None = Field(default=None, description="ISIN 코드 (12자리)")

    @field_validator("item_name", "like_item_name", "short_code", "isin_cd")
    @classmethod
    def _strip_product(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        return v or None


class MarketIndex(BaseModel):
    """주가지수 일별 시세 한 건."""

    bas_dt: str = Field(description="기준일자 (YYYYMMDD)")
    index_name: str = Field(description="지수명 (예: 코스피, 코스닥)")
    index_class: str | None = Field(
        default=None, description="지수 계열 (예: KOSPI시리즈)"
    )
    component_count: int | None = Field(default=None, description="구성 종목 수")
    close: float | None = Field(default=None, description="종가")
    change: float | None = Field(default=None, description="전일 대비 등락")
    change_rate: float | None = Field(default=None, description="전일 대비 등락률 (%)")
    open: float | None = Field(default=None, description="시가")
    high: float | None = Field(default=None, description="고가")
    low: float | None = Field(default=None, description="저가")
    volume: int | None = Field(default=None, description="거래량")
    trade_value: int | None = Field(default=None, description="거래대금 (원)")
    listed_market_cap: int | None = Field(default=None, description="상장시가총액 (원)")
    year_high: float | None = Field(default=None, description="연중 최고 지수")
    year_high_date: str | None = Field(default=None, description="연중 최고 일자")
    year_low: float | None = Field(default=None, description="연중 최저 지수")
    year_low_date: str | None = Field(default=None, description="연중 최저 일자")
    base_point_date: str | None = Field(default=None, description="기준 시점")
    base_index: float | None = Field(default=None, description="기준 지수")

    @classmethod
    def from_api(cls, raw: dict) -> "MarketIndex":
        """API camelCase 항목 → 모델."""
        return cls(
            bas_dt=raw.get("basDt") or "",
            index_name=raw.get("idxNm") or "",
            index_class=raw.get("idxCsf") or None,
            component_count=_int_or_none(raw.get("epyItmsCnt")),
            close=_float_or_none(raw.get("clpr")),
            change=_float_or_none(raw.get("vs")),
            change_rate=_float_or_none(raw.get("fltRt")),
            open=_float_or_none(raw.get("mkp")),
            high=_float_or_none(raw.get("hipr")),
            low=_float_or_none(raw.get("lopr")),
            volume=_int_or_none(raw.get("trqu")),
            trade_value=_int_or_none(raw.get("trPrc")),
            listed_market_cap=_int_or_none(raw.get("lstgMrktTotAmt")),
            year_high=_float_or_none(raw.get("yrWRcrdHgst")),
            year_high_date=raw.get("yrWRcrdHgstDt") or None,
            year_low=_float_or_none(raw.get("yrWRcrdLwst")),
            year_low_date=raw.get("yrWRcrdLwstDt") or None,
            base_point_date=raw.get("basPntm") or None,
            base_index=_float_or_none(raw.get("basIdx")),
        )


class BondIndex(BaseModel):
    """채권지수 일별 시세 한 건. 주가지수와 필드가 완전히 다르다."""

    bas_dt: str = Field(description="기준일자 (YYYYMMDD)")
    index_name: str = Field(description="지수명 (예: KRX 채권지수)")
    total_return_index: float | None = Field(
        default=None, description="총수익지수 종가"
    )
    total_return_change: float | None = Field(
        default=None, description="총수익지수 대비"
    )
    zero_reinvest_index: float | None = Field(
        default=None, description="제로재투자지수 종가"
    )
    call_reinvest_index: float | None = Field(
        default=None, description="콜재투자지수 종가"
    )
    market_price_index: float | None = Field(
        default=None, description="시장가격지수 종가"
    )
    net_price_index: float | None = Field(default=None, description="순가격지수 종가")
    duration: float | None = Field(default=None, description="듀레이션")
    convexity: float | None = Field(default=None, description="컨벡시티")
    ytm: float | None = Field(default=None, description="만기수익률 (%)")

    @classmethod
    def from_api(cls, raw: dict) -> "BondIndex":
        """API camelCase 항목 → 모델."""
        return cls(
            bas_dt=raw.get("basDt") or "",
            index_name=raw.get("idxNm") or "",
            total_return_index=_float_or_none(raw.get("totBnfIdxClpr")),
            total_return_change=_float_or_none(raw.get("totBnfIdxVs")),
            zero_reinvest_index=_float_or_none(raw.get("zrRinvIdxClpr")),
            call_reinvest_index=_float_or_none(raw.get("clRinvIdxClpr")),
            market_price_index=_float_or_none(raw.get("mrktPrcIdxClpr")),
            net_price_index=_float_or_none(raw.get("nPrcIdxClpr")),
            duration=_float_or_none(raw.get("durt")),
            convexity=_float_or_none(raw.get("cnvt")),
            ytm=_float_or_none(raw.get("ytm")),
        )


class ProductPrice(BaseModel):
    """ETF·ETN 일별 시세 한 건. ETF 는 순자산가치(nav), ETN 은 지표가치를 쓴다."""

    bas_dt: str = Field(description="기준일자 (YYYYMMDD)")
    short_code: str = Field(description="단축코드 (영숫자 6자리)")
    isin_cd: str | None = Field(default=None, description="ISIN 코드")
    item_name: str = Field(description="종목명")
    close: int | None = Field(default=None, description="종가 (원)")
    change: int | None = Field(default=None, description="전일 대비 (원)")
    change_rate: float | None = Field(default=None, description="전일 대비 등락률 (%)")
    nav: float | None = Field(default=None, description="순자산가치 NAV (ETF)")
    indicative_value: float | None = Field(default=None, description="지표가치 (ETN)")
    open: int | None = Field(default=None, description="시가 (원)")
    high: int | None = Field(default=None, description="고가 (원)")
    low: int | None = Field(default=None, description="저가 (원)")
    volume: int | None = Field(default=None, description="거래량")
    trade_value: int | None = Field(default=None, description="거래대금 (원)")
    market_cap: int | None = Field(default=None, description="시가총액 (원)")
    listed_count: int | None = Field(default=None, description="상장 증권수")
    net_asset_total: int | None = Field(
        default=None, description="순자산총액·지표가치총액 (원)"
    )
    base_index_name: str | None = Field(default=None, description="기초지수 이름")
    base_index_close: float | None = Field(default=None, description="기초지수 종가")

    @classmethod
    def from_api(cls, raw: dict) -> "ProductPrice":
        """API camelCase 항목 → 모델. ETF/ETN 이 서로 다른 이름을 쓰는 필드를 모은다."""
        return cls(
            bas_dt=raw.get("basDt") or "",
            short_code=raw.get("srtnCd") or "",
            isin_cd=raw.get("isinCd") or None,
            item_name=raw.get("itmsNm") or "",
            close=_int_or_none(raw.get("clpr")),
            change=_int_or_none(raw.get("vs")),
            change_rate=_float_or_none(raw.get("fltRt")),
            nav=_float_or_none(raw.get("nav")),
            indicative_value=_float_or_none(raw.get("indcVal")),
            open=_int_or_none(raw.get("mkp")),
            high=_int_or_none(raw.get("hipr")),
            low=_int_or_none(raw.get("lopr")),
            volume=_int_or_none(raw.get("trqu")),
            trade_value=_int_or_none(raw.get("trPrc")),
            market_cap=_int_or_none(raw.get("mrktTotAmt")),
            listed_count=_int_or_none(raw.get("stLstgCnt") or raw.get("lstgScrtCnt")),
            net_asset_total=_int_or_none(
                raw.get("nPptTotAmt") or raw.get("indcValTotAmt")
            ),
            base_index_name=raw.get("bssIdxIdxNm") or None,
            base_index_close=_float_or_none(raw.get("bssIdxClpr")),
        )
