"""Data models for National Pension Service API."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BusinessSearchRequest(BaseModel):
    """사업장 정보조회 요청 모델."""

    ldong_addr_mgpl_dg_cd: Optional[str] = Field(
        default=None, description="법정동주소광역시도코드"
    )
    ldong_addr_mgpl_sggu_cd: Optional[str] = Field(
        default=None, description="법정동주소시군구코드"
    )
    ldong_addr_mgpl_sggu_emd_cd: Optional[str] = Field(
        default=None, description="법정동주소읍면동코드"
    )
    wkpl_nm: Optional[str] = Field(default=None, description="사업장명")
    bzowr_rgst_no: Optional[str] = Field(default=None, description="사업자등록번호(앞6자리)")
    data_type: str = Field("json", description="응답자료형식(xml/json)")
    page_no: int = Field(1, description="페이지번호")
    num_of_rows: int = Field(10, description="한 페이지 결과 수")


class BusinessItem(BaseModel):
    """사업장 기본정보 아이템."""

    data_crt_ym: Optional[str] = Field(default=None, alias="dataCrtYm", description="자료생성년월")
    seq: Optional[int] = Field(default=None, description="식별번호")
    wkpl_nm: Optional[str] = Field(default=None, alias="wkplNm", description="사업장명")
    bzowr_rgst_no: Optional[str] = Field(
        default=None, alias="bzowrRgstNo", description="사업자등록번호"
    )
    wkpl_road_nm_dtl_addr: Optional[str] = Field(
        None, alias="wkplRoadNmDtlAddr", description="사업장도로명상세주소"
    )
    wkpl_jnng_stcd: Optional[str] = Field(
        None, alias="wkplJnngStcd", description="사업장가입상태코드(1:등록,2:탈퇴)"
    )
    wkpl_styl_dvcd: Optional[str] = Field(
        None, alias="wkplStylDvcd", description="사업장형태구분코드(1:법인,2:개인)"
    )
    ldong_addr_mgpl_dg_cd: Optional[str] = Field(
        None, alias="ldongAddrMgplDgCd", description="법정동주소광역시도코드"
    )
    ldong_addr_mgpl_sggu_cd: Optional[str] = Field(
        None, alias="ldongAddrMgplSgguCd", description="법정동주소시군구코드"
    )
    ldong_addr_mgpl_sggu_emd_cd: Optional[str] = Field(
        None, alias="ldongAddrMgplSgguEmdCd", description="법정동주소읍면동코드"
    )

    model_config = ConfigDict(populate_by_name=True)


class BusinessDetailItem(BaseModel):
    """사업장 상세정보 아이템."""

    wkpl_nm: Optional[str] = Field(default=None, alias="wkplNm", description="사업장명")
    bzowr_rgst_no: Optional[str] = Field(
        default=None, alias="bzowrRgstNo", description="사업자등록번호"
    )
    wkpl_road_nm_dtl_addr: Optional[str] = Field(
        None, alias="wkplRoadNmDtlAddr", description="사업장도로명상세주소"
    )
    wkpl_jnng_stcd: Optional[str] = Field(
        None, alias="wkplJnngStcd", description="사업장가입상태코드"
    )
    ldong_addr_mgpl_dg_cd: Optional[str] = Field(
        None, alias="ldongAddrMgplDgCd", description="법정동주소광역시도코드"
    )
    ldong_addr_mgpl_sggu_cd: Optional[str] = Field(
        None, alias="ldongAddrMgplSgguCd", description="법정동주소시군구코드"
    )
    ldong_addr_mgpl_sggu_emd_cd: Optional[str] = Field(
        None, alias="ldongAddrMgplSgguEmdCd", description="법정동주소읍면동코드"
    )
    wkpl_styl_dvcd: Optional[str] = Field(
        None, alias="wkplStylDvcd", description="사업장형태구분코드"
    )
    wkpl_intp_cd: Optional[str] = Field(
        default=None, alias="wkplIntpCd", description="사업업종코드"
    )
    vldt_vl_krn_nm: Optional[str] = Field(
        None, alias="vldtVlKrnNm", description="사업장업종코드명"
    )
    adpt_dt: Optional[str] = Field(default=None, alias="adptDt", description="사업장등록일")
    scsn_dt: Optional[str] = Field(default=None, alias="scsnDt", description="사업장탈퇴일")
    jnngp_cnt: Optional[int] = Field(default=None, alias="jnngpCnt", description="가입자수")
    crrmm_ntc_amt: Optional[str] = Field(
        default=None, alias="crrmmNtcAmt", description="당월고지금액"
    )

    model_config = ConfigDict(populate_by_name=True)


class PeriodStatusItem(BaseModel):
    """기간별 현황 정보 아이템."""

    nw_acqzr_cnt: Optional[int] = Field(
        default=None, alias="nwAcqzrCnt", description="월별 취득자수"
    )
    lss_jnngp_cnt: Optional[int] = Field(
        default=None, alias="lssJnngpCnt", description="월별 상실자수"
    )

    model_config = ConfigDict(populate_by_name=True)


class APIResponse(BaseModel):
    """API 응답 공통 모델."""

    result_code: str = Field(..., alias="resultCode")
    result_msg: str = Field(..., alias="resultMsg")
    page_no: Optional[int] = Field(default=None, alias="pageNo")
    num_of_rows: Optional[int] = Field(default=None, alias="numOfRows")
    total_count: Optional[int] = Field(default=None, alias="totalCount")
    items: Optional[List] = None

    model_config = ConfigDict(populate_by_name=True)


class RegionCodeItem(BaseModel):
    """법정동코드 아이템 (행정안전부 행정표준코드 StanReginCd)."""

    model_config = ConfigDict(populate_by_name=True)

    region_cd: str = Field(description="법정동코드 (10자리)")
    name: str = Field(alias="locatadd_nm", description="지역주소명 (예: 서울특별시 강남구 역삼동)")
    sido_cd: str = Field(description="시도코드 (2자리)")
    sgg_cd: str = Field(description="시군구코드 (3자리, 시도 단위면 000)")
    umd_cd: str = Field(description="읍면동코드 (3자리, 시군구 단위면 000)")
    ri_cd: str = Field(description="리코드 (2자리, 리가 아니면 00)")
    parent_cd: Optional[str] = Field(
        default=None, alias="locathigh_cd", description="상위 법정동코드"
    )


INSURANCE_KINDS = {"1": "산재", "2": "고용"}


class InsuredWorkplace(BaseModel):
    """고용·산재보험 가입 사업장 한 건 (근로복지공단 gySjbPstateInfoService)."""

    insurance: str = Field(description="보험 구분 (산재/고용)")
    workplace_nm: str = Field(description="사업장명")
    bzno: str = Field(description="사업자등록번호")
    addr: Optional[str] = Field(default=None, description="주소")
    post: Optional[str] = Field(default=None, description="우편번호")
    employee_cnt: Optional[int] = Field(default=None, description="상시인원")
    established_dt: Optional[str] = Field(default=None, description="보험관계 성립일 (YYYYMMDD)")
    industry_cd: Optional[str] = Field(
        default=None, description="업종코드 (산재: sjEopjongCd, 고용: gyEopjongCd)"
    )
    industry_nm: Optional[str] = Field(default=None, description="업종명")
    saeop_fg: Optional[str] = Field(default=None, description="사업구분 코드 (원본 saeopFg)")

    @classmethod
    def from_api(cls, raw: dict) -> "InsuredWorkplace":
        """XML 항목(문자열 값) → 모델. 업종은 보험 구분에 따라 다른 요소에 온다."""

        def s(key: str) -> Optional[str]:
            v = raw.get(key)
            v = v.strip() if isinstance(v, str) else v
            return v or None

        kind = INSURANCE_KINDS.get(
            str(raw.get("opaBoheomFg", "")), str(raw.get("opaBoheomFg", ""))
        )
        cnt = s("sangsiInwonCnt")
        return cls(
            insurance=kind,
            workplace_nm=s("saeopjangNm") or "",
            bzno=s("saeopjaDrno") or "",
            addr=s("addr"),
            post=s("post"),
            employee_cnt=int(cnt) if cnt is not None and cnt.isdigit() else None,
            established_dt=s("seongripDt"),
            industry_cd=s("sjEopjongCd") or s("gyEopjongCd"),
            industry_nm=s("sjEopjongNm") or s("gyEopjongNm"),
            saeop_fg=s("saeopFg"),
        )
