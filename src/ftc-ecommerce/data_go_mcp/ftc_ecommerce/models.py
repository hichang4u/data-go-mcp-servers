"""Models for 공정거래위원회 통신판매사업자.

빈 값이 ``"N/A"`` 문자열로 오므로 ``clean()`` 을 거치지 않은 값을 모델에 넣지 않는다.
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# 이 API 가 빈 값을 표현하는 방법들. ``"NULL"`` 이 흔하다 — 실응답 100행 중 29행의
# rprsvEmladr 가 이 문자열이었다 (2026-10-03).
EMPTY_VALUES = {"", "n/a", "na", "null", "none", "-"}

# 영업 중으로 볼 상태. 나머지는 직권말소·직권취소·폐업 등
ACTIVE_STATUS = "정상영업"


def clean(value: Any) -> Optional[str]:
    """``"N/A"``·공백을 ``None`` 으로."""
    text = str(value).strip() if value is not None else ""
    return None if text.lower() in EMPTY_VALUES else text


def to_iso_date(value: Any) -> Optional[str]:
    """``"20130821"`` → ``"2013-08-21"``. 형식이 다르면 원문."""
    text = clean(value)
    if not text or len(text) != 8 or not text.isdigit():
        return text
    return f"{text[:4]}-{text[4:6]}-{text[6:]}"


def split_domains(value: Any) -> list[str]:
    """도메인은 공백으로 이어 붙어 온다 (``"http://a  http://b"``)."""
    text = clean(value)
    return text.split() if text else []


class OnlineSeller(BaseModel):
    """통신판매사업자 신고 한 건."""

    model_config = ConfigDict(populate_by_name=True)

    business_number: Optional[str] = Field(default=None, description="사업자등록번호")
    corporate_number: Optional[str] = Field(
        default=None, description="법인등록번호. fsc 재무제표 툴의 crno 로 그대로 쓴다"
    )
    name: Optional[str] = Field(default=None, description="상호")
    representative: Optional[str] = Field(default=None, description="대표자")
    corporation: Optional[bool] = Field(default=None, description="법인 여부 (개인이면 False)")
    operating_status: Optional[str] = Field(
        default=None, description="영업상태 (정상영업/직권말소/직권취소 등)"
    )
    business_status: Optional[str] = Field(
        default=None, description="사업자 상태 (계속사업자/폐업자)"
    )
    active: Optional[bool] = Field(default=None, description="지금 정상영업인가")
    report_number: Optional[str] = Field(default=None, description="통신판매업 신고번호")
    reported_on: Optional[str] = Field(default=None, description="신고일 (YYYY-MM-DD)")
    reported_to: Optional[str] = Field(default=None, description="신고기관")
    region: Optional[str] = Field(default=None, description="시도")
    address: Optional[str] = Field(default=None, description="사업장 주소 (지번)")
    road_address: Optional[str] = Field(default=None, description="사업장 주소 (도로명)")
    postal_code: Optional[str] = Field(default=None, description="우편번호")
    phone: Optional[str] = Field(default=None, description="전화번호")
    fax: Optional[str] = Field(default=None, description="팩스번호")
    email: Optional[str] = Field(default=None, description="대표자 이메일")
    domains: list[str] = Field(default_factory=list, description="신고된 인터넷 도메인")
    sales_method: Optional[str] = Field(default=None, description="판매방식 (인터넷 등)")
    product_type: Optional[str] = Field(default=None, description="취급품목 (종합몰 등)")
    server_location: Optional[str] = Field(default=None, description="호스팅 서버 소재지")
    closed_on: Optional[str] = Field(default=None, description="폐업일")
    suspended_from: Optional[str] = Field(default=None, description="휴업 시작일")
    suspended_until: Optional[str] = Field(default=None, description="휴업 종료일")
    resumed_on: Optional[str] = Field(default=None, description="영업 재개일")
    department: Optional[str] = Field(default=None, description="처리 담당부서")
    department_phone: Optional[str] = Field(default=None, description="담당부서 전화번호")
    updated_on: Optional[str] = Field(default=None, description="자료 수정일")

    @classmethod
    def from_api(cls, row: dict[str, Any]) -> "OnlineSeller":
        """응답 한 행을 정규화한다."""
        corp = clean(row.get("corpYnNm"))
        status = clean(row.get("operSttusCdNm"))
        return cls(
            business_number=clean(row.get("brno")),
            corporate_number=clean(row.get("crno")),
            name=clean(row.get("bzmnNm")),
            representative=clean(row.get("rprsvNm")),
            corporation=(corp == "법인") if corp else None,
            operating_status=status,
            business_status=clean(row.get("bzmnRgsSttusSeNm")),
            active=(status == ACTIVE_STATUS) if status else None,
            report_number=clean(row.get("prmmiMnno")),
            reported_on=to_iso_date(row.get("dclrDate")),
            reported_to=clean(row.get("dclrInstNm")),
            region=clean(row.get("ctpvNm")),
            address=clean(row.get("lctnAddr")),
            road_address=clean(row.get("lctnRnAddr")),
            postal_code=clean(row.get("lctnRnOzip")),
            phone=clean(row.get("telno")),
            fax=clean(row.get("fxno")),
            email=clean(row.get("rprsvEmladr")),
            domains=split_domains(row.get("domnCn")),
            sales_method=clean(row.get("ntslMthdCn")),
            product_type=clean(row.get("ntslPrdlstCn")),
            server_location=clean(row.get("opnServerPlaceAladr")),
            closed_on=to_iso_date(row.get("clsbizDate")),
            suspended_from=to_iso_date(row.get("tcbizBgngDate")),
            suspended_until=to_iso_date(row.get("tcbizEndDate")),
            resumed_on=to_iso_date(row.get("bsnResmptDate")),
            department=clean(row.get("prcsDeptDtlNm")),
            department_phone=clean(row.get("chrgDeptTelno")),
            updated_on=to_iso_date(str(row.get("opnMdfcnDt") or "")[:8]),
        )
