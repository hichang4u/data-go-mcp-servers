"""고용24 채용정보 응답 모델.

목록(``wanted``)과 상세(``wantedDtl``)의 필드 이름이 서로 다르다 (``company`` vs ``corpNm``,
``title`` vs ``wantedTitle``). 금액·인원은 ``"453 백만원"``, ``"25 명"`` 처럼 단위가 붙은
문자열로 와서 숫자로 바꿀 수 없는 것은 원문을 살린다.
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


def clean(value: Any) -> Optional[str]:
    """빈 문자열·공백은 ``None``. XML 빈 요소가 ``None`` 으로 오는 것도 처리."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text or None


def to_int(value: Any) -> Optional[int]:
    """``"41000000"`` → ``41000000``. 단위가 붙었으면 ``None``."""
    text = (clean(value) or "").replace(",", "")
    try:
        return int(text)
    except ValueError:
        return None


def to_date(value: Any) -> Optional[str]:
    """``"26-10-01"`` → ``"2026-10-01"``. 다른 형식은 원문."""
    text = clean(value)
    if not text:
        return None
    parts = text.split("-")
    if len(parts) == 3 and len(parts[0]) == 2 and all(p.isdigit() for p in parts):
        return f"20{parts[0]}-{parts[1]}-{parts[2]}"
    return text


class JobPosting(BaseModel):
    """채용공고 한 건 (목록)."""

    model_config = ConfigDict(populate_by_name=True)

    wanted_auth_no: Optional[str] = Field(
        default=None, description="채용공고 번호 (상세 조회에 쓴다)"
    )
    company: Optional[str] = Field(default=None, description="회사명")
    business_number: Optional[str] = Field(default=None, description="사업자등록번호 10자리")
    title: Optional[str] = Field(default=None, description="공고 제목")
    industry: Optional[str] = Field(default=None, description="업종")
    region: Optional[str] = Field(default=None, description="근무지역")
    address: Optional[str] = Field(default=None, description="근무지 주소")
    salary_type: Optional[str] = Field(default=None, description="임금 형태 (연봉/월급 등)")
    salary: Optional[str] = Field(default=None, description="임금 (표시용 문자열)")
    min_salary: Optional[int] = Field(default=None, description="최저 임금 (원)")
    max_salary: Optional[int] = Field(default=None, description="최고 임금 (원, 0이면 미지정)")
    career: Optional[str] = Field(default=None, description="경력 구분 (신입/경력)")
    education: Optional[str] = Field(default=None, description="학력 (최저~최고)")
    holiday: Optional[str] = Field(default=None, description="근무 형태")
    posted_date: Optional[str] = Field(default=None, description="등록일 (YYYY-MM-DD)")
    close_date: Optional[str] = Field(default=None, description="마감일")
    job_code: Optional[str] = Field(default=None, description="직종 코드")
    employment_type_code: Optional[str] = Field(default=None, description="고용형태 코드")
    info_service: Optional[str] = Field(
        default=None, description="정보제공처 (상세 조회의 infoSvc 로 쓰인다)"
    )
    url: Optional[str] = Field(default=None, description="공고 상세 페이지 주소")

    @classmethod
    def from_api(cls, row: dict[str, Any]) -> "JobPosting":
        """목록 XML 한 행을 정규화한다."""
        education = " ~ ".join(
            p for p in (clean(row.get("minEdubg")), clean(row.get("maxEdubg"))) if p
        )
        address = " ".join(
            p for p in (clean(row.get("basicAddr")), clean(row.get("detailAddr"))) if p
        )
        return cls(
            wanted_auth_no=clean(row.get("wantedAuthNo")),
            company=clean(row.get("company")),
            business_number=clean(row.get("busino")),
            title=clean(row.get("title")),
            industry=clean(row.get("indTpNm")),
            region=clean(row.get("region")),
            address=address or None,
            salary_type=clean(row.get("salTpNm")),
            salary=clean(row.get("sal")),
            min_salary=to_int(row.get("minSal")),
            max_salary=to_int(row.get("maxSal")),
            career=clean(row.get("career")),
            education=education or None,
            holiday=clean(row.get("holidayTpNm")),
            posted_date=to_date(row.get("regDt")),
            close_date=clean(row.get("closeDt")),
            job_code=clean(row.get("jobsCd")),
            employment_type_code=clean(row.get("empTpCd")),
            info_service=clean(row.get("infoSvc")),
            url=clean(row.get("wantedInfoUrl")),
        )


class CompanyProfile(BaseModel):
    """상세의 기업 정보. 비상장사는 금융위 재무정보에 없어 여기가 유일한 규모 자료다."""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(default=None, description="회사명")
    ceo_name: Optional[str] = Field(default=None, description="대표자명")
    employee_count: Optional[str] = Field(default=None, description="전체 종업원 수 (예: 25 명)")
    capital: Optional[str] = Field(default=None, description="자본금 (예: 453 백만원)")
    annual_sales: Optional[str] = Field(default=None, description="연 매출액 (예: 5745 백만원)")
    industry: Optional[str] = Field(default=None, description="업종")
    business_content: Optional[str] = Field(default=None, description="사업 내용")
    address: Optional[str] = Field(default=None, description="회사 주소")
    homepage: Optional[str] = Field(default=None, description="홈페이지")
    size: Optional[str] = Field(default=None, description="기업 규모 (중소기업 등)")

    @classmethod
    def from_api(cls, row: dict[str, Any]) -> "CompanyProfile":
        """상세 XML 의 ``corpInfo`` 를 정규화한다."""
        return cls(
            name=clean(row.get("corpNm")),
            ceo_name=clean(row.get("reperNm")),
            employee_count=clean(row.get("totPsncnt")),
            capital=clean(row.get("capitalAmt")),
            annual_sales=clean(row.get("yrSalesAmt")),
            industry=clean(row.get("indTpCdNm")),
            business_content=clean(row.get("busiCont")),
            address=clean(row.get("corpAddr")),
            homepage=clean(row.get("homePg")),
            size=clean(row.get("busiSize")),
        )


class JobDetail(BaseModel):
    """상세의 채용 정보."""

    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = Field(default=None, description="공고 제목")
    job_name: Optional[str] = Field(default=None, description="직종명 (코드 포함)")
    job_content: Optional[str] = Field(default=None, description="담당 업무")
    related_jobs: Optional[str] = Field(default=None, description="관련 직종")
    hiring_count: Optional[str] = Field(default=None, description="모집 인원")
    employment_type: Optional[str] = Field(default=None, description="고용 형태")
    salary: Optional[str] = Field(default=None, description="임금 조건")
    career: Optional[str] = Field(default=None, description="경력 조건")
    education: Optional[str] = Field(default=None, description="학력 조건")
    major: Optional[str] = Field(default=None, description="전공")
    certificate: Optional[str] = Field(default=None, description="자격증")
    foreign_language: Optional[str] = Field(default=None, description="외국어")
    computer_skill: Optional[str] = Field(default=None, description="전산 활용 능력")
    preference: Optional[str] = Field(default=None, description="우대 조건")
    close_date: Optional[str] = Field(default=None, description="접수 마감일")

    @classmethod
    def from_api(cls, row: dict[str, Any]) -> "JobDetail":
        """상세 XML 의 ``wantedInfo`` 를 정규화한다."""
        return cls(
            title=clean(row.get("wantedTitle")),
            job_name=clean(row.get("jobsNm")),
            job_content=clean(row.get("jobCont")),
            related_jobs=clean(row.get("relJobsNm")),
            hiring_count=clean(row.get("collectPsncnt")),
            employment_type=clean(row.get("empTpNm")),
            salary=clean(row.get("salTpNm")),
            career=clean(row.get("enterTpNm")),
            education=clean(row.get("eduNm")),
            major=clean(row.get("major")),
            certificate=clean(row.get("certificate")),
            foreign_language=clean(row.get("forLang")),
            computer_skill=clean(row.get("compAbl")),
            preference=clean(row.get("pfCond")) or clean(row.get("etcPfCond")),
            close_date=clean(row.get("receiptCloseDt")),
        )
