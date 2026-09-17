"""OpenDART 응답 모델.

OpenDART 는 필드명이 이미 snake_case 라 alias 가 필요 없다. 금액은 문자열(쉼표 있거나 없음)로 오므로
정수로 바꾸고, ``"-"`` / ``""`` 는 ``None`` 으로 정리한다.
"""

from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


CORP_CLS_NAMES = {"Y": "유가증권시장", "K": "코스닥", "N": "코넥스", "E": "기타"}

# 공시유형 (list.json pblntf_ty)
PBLNTF_TYPES = {
    "A": "정기공시",
    "B": "주요사항보고",
    "C": "발행공시",
    "D": "지분공시",
    "E": "기타공시",
    "F": "외부감사관련",
    "G": "펀드공시",
    "H": "자산유동화",
    "I": "거래소공시",
    "J": "공정위공시",
}

# 보고서 코드 (bsns_year 와 함께)
REPRT_CODES = {
    "11011": "사업보고서",
    "11012": "반기보고서",
    "11013": "1분기보고서",
    "11014": "3분기보고서",
}

FS_DIVS = {"CFS": "연결재무제표", "OFS": "재무제표(별도)"}

SJ_DIVS = {
    "BS": "재무상태표",
    "IS": "손익계산서",
    "CIS": "포괄손익계산서",
    "CF": "현금흐름표",
    "SCE": "자본변동표",
}


def _blank_to_none(value: object) -> object:
    if isinstance(value, str) and value.strip() in ("", "-"):
        return None
    return value


Amount = Optional[Union[int, float]]


def _to_amount(value: object) -> Amount:
    """``"514,531,948,000,000"`` / ``"514531948000000"`` → int. 빈 값·``-`` 는 None.

    소수(주당 지표 등)는 float. 파싱이 안 되는 값은 None — 한 셀 때문에 호출 전체가 실패하지 않도록.
    """
    if value is None or isinstance(value, (int, float)):
        return value
    text = str(value).replace(",", "").strip()
    if text in ("", "-"):
        return None
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return None


class Company(BaseModel):
    """company.json — 기업 개황."""

    model_config = ConfigDict(populate_by_name=True)

    corp_code: str = Field(description="고유번호 (8자리)")
    corp_name: Optional[str] = Field(default=None, description="정식명칭")
    corp_name_eng: Optional[str] = Field(default=None, description="영문명칭")
    stock_name: Optional[str] = Field(default=None, description="종목명 (상장사) 또는 약식명칭")
    stock_code: Optional[str] = Field(default=None, description="종목코드 (6자리, 비상장은 빈 값)")
    ceo_nm: Optional[str] = Field(default=None, description="대표자명")
    corp_cls: Optional[str] = Field(
        default=None, description="법인구분 Y유가/K코스닥/N코넥스/E기타"
    )
    corp_cls_name: Optional[str] = Field(default=None, description="법인구분 이름")
    jurir_no: Optional[str] = Field(default=None, description="법인등록번호 (13자리)")
    bizr_no: Optional[str] = Field(default=None, description="사업자등록번호 (10자리)")
    adres: Optional[str] = Field(default=None, description="주소")
    hm_url: Optional[str] = Field(default=None, description="홈페이지")
    ir_url: Optional[str] = Field(default=None, description="IR 홈페이지")
    phn_no: Optional[str] = Field(default=None, description="전화번호")
    fax_no: Optional[str] = Field(default=None, description="팩스번호")
    induty_code: Optional[str] = Field(default=None, description="업종코드")
    est_dt: Optional[str] = Field(default=None, description="설립일 (YYYYMMDD)")
    acc_mt: Optional[str] = Field(default=None, description="결산월 (MM)")

    @field_validator("stock_code", "ir_url", "hm_url", "fax_no", mode="before")
    @classmethod
    def _blank(cls, value: object) -> object:
        return _blank_to_none(value)

    def model_post_init(self, __context: object) -> None:
        """corp_cls 코드에서 이름을 채운다."""
        if self.corp_cls and not self.corp_cls_name:
            self.corp_cls_name = CORP_CLS_NAMES.get(self.corp_cls)


class Disclosure(BaseModel):
    """list.json 의 한 건."""

    model_config = ConfigDict(populate_by_name=True)

    rcept_no: str = Field(description="접수번호 (14자리). get_disclosure_document 입력")
    corp_code: Optional[str] = Field(default=None, description="고유번호")
    corp_name: Optional[str] = Field(default=None, description="회사명")
    stock_code: Optional[str] = Field(default=None, description="종목코드")
    corp_cls: Optional[str] = Field(default=None, description="법인구분 Y/K/N/E")
    report_nm: Optional[str] = Field(default=None, description="보고서명")
    flr_nm: Optional[str] = Field(default=None, description="공시 제출인명")
    rcept_dt: Optional[str] = Field(default=None, description="접수일자 (YYYYMMDD)")
    rm: Optional[str] = Field(
        default=None,
        description="비고: 유(유가증권시장) 코(코스닥) 채(채권) 넥(코넥스) 공(공정위) 연(연결부분) 정(정정) 철(철회)",
    )

    @field_validator("report_nm", "corp_name", "flr_nm", "stock_code", "rm", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
        return _blank_to_none(value)


class KeyAccount(BaseModel):
    """fnlttSinglAcnt.json — 주요계정 한 행."""

    model_config = ConfigDict(populate_by_name=True)

    rcept_no: Optional[str] = Field(default=None, description="접수번호")
    bsns_year: Optional[str] = Field(default=None, description="사업연도")
    reprt_code: Optional[str] = Field(default=None, description="보고서 코드")
    fs_div: Optional[str] = Field(default=None, description="CFS 연결 / OFS 별도")
    fs_nm: Optional[str] = Field(default=None, description="재무제표 구분명")
    sj_div: Optional[str] = Field(default=None, description="BS 재무상태표 / IS 손익계산서")
    sj_nm: Optional[str] = Field(default=None, description="재무제표명")
    account_nm: Optional[str] = Field(default=None, description="계정명")
    thstrm_nm: Optional[str] = Field(default=None, description="당기명 (예: 제 56 기)")
    thstrm_dt: Optional[str] = Field(default=None, description="당기 기준일/기간")
    thstrm_amount: Amount = Field(default=None, description="당기 금액")
    frmtrm_nm: Optional[str] = Field(default=None, description="전기명")
    frmtrm_dt: Optional[str] = Field(default=None, description="전기 기준일/기간")
    frmtrm_amount: Amount = Field(default=None, description="전기 금액")
    bfefrmtrm_nm: Optional[str] = Field(default=None, description="전전기명")
    bfefrmtrm_dt: Optional[str] = Field(default=None, description="전전기 기준일/기간")
    bfefrmtrm_amount: Amount = Field(default=None, description="전전기 금액")
    ord: Optional[int] = Field(default=None, description="계정 표시 순서")
    currency: Optional[str] = Field(default=None, description="통화")

    @field_validator("thstrm_amount", "frmtrm_amount", "bfefrmtrm_amount", "ord", mode="before")
    @classmethod
    def _amount(cls, value: object) -> Amount:
        return _to_amount(value)


class FinancialStatementItem(BaseModel):
    """fnlttSinglAcntAll.json — 전체 재무제표 한 행 (XBRL 계정 ID 포함)."""

    model_config = ConfigDict(populate_by_name=True)

    rcept_no: Optional[str] = Field(default=None, description="접수번호")
    bsns_year: Optional[str] = Field(default=None, description="사업연도")
    reprt_code: Optional[str] = Field(default=None, description="보고서 코드")
    sj_div: Optional[str] = Field(default=None, description="BS/IS/CIS/CF/SCE")
    sj_nm: Optional[str] = Field(default=None, description="재무제표명")
    account_id: Optional[str] = Field(
        default=None, description="XBRL 계정 ID (예: ifrs-full_Assets)"
    )
    account_nm: Optional[str] = Field(default=None, description="계정명")
    account_detail: Optional[str] = Field(default=None, description="계정 상세 (자본변동표 등)")
    thstrm_nm: Optional[str] = Field(default=None, description="당기명")
    thstrm_amount: Amount = Field(default=None, description="당기 금액")
    thstrm_add_amount: Amount = Field(default=None, description="당기 누적 금액 (분기·반기)")
    frmtrm_nm: Optional[str] = Field(default=None, description="전기명")
    frmtrm_amount: Amount = Field(default=None, description="전기 금액")
    frmtrm_q_nm: Optional[str] = Field(default=None, description="전기 분기명")
    frmtrm_q_amount: Amount = Field(default=None, description="전기 분기 금액")
    frmtrm_add_amount: Amount = Field(default=None, description="전기 누적 금액")
    bfefrmtrm_nm: Optional[str] = Field(default=None, description="전전기명")
    bfefrmtrm_amount: Amount = Field(default=None, description="전전기 금액")
    ord: Optional[int] = Field(default=None, description="계정 표시 순서")
    currency: Optional[str] = Field(default=None, description="통화")

    @field_validator(
        "thstrm_amount",
        "thstrm_add_amount",
        "frmtrm_amount",
        "frmtrm_q_amount",
        "frmtrm_add_amount",
        "bfefrmtrm_amount",
        "ord",
        mode="before",
    )
    @classmethod
    def _amount(cls, value: object) -> Amount:
        return _to_amount(value)

    @field_validator("account_detail", mode="before")
    @classmethod
    def _detail(cls, value: object) -> object:
        return _blank_to_none(value)
