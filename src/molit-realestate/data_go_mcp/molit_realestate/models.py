"""국토교통부 실거래가 응답 모델.

종류(아파트/오피스텔/연립다세대/단독다가구/상업업무용/토지)마다 필드 이름과 개수가 다르다
(2026-09-30 실호출 확인). 공통으로 쓸 수 있는 것만 같은 이름으로 모으고, 면적처럼 **뜻이 다른
값은 뭉뚱그리지 않고** 각각 둔다 (전용면적/연면적/대지면적/거래면적).
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


def to_int(value: Any) -> Optional[int]:
    """``"790,000"`` → ``790000``. 빈 값·숫자가 아니면 ``None``."""
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    try:
        return int(text)
    except ValueError:
        return None


def to_float(value: Any) -> Optional[float]:
    """``"147.41"`` → ``147.41``. 빈 값·숫자가 아니면 ``None``."""
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def clean(value: Any) -> Optional[str]:
    """XML 의 빈 요소는 공백 한 칸으로 온다 → ``None``."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def to_date(year: Any, month: Any, day: Any) -> Optional[str]:
    """``2026`` ``8`` ``29`` → ``"2026-08-29"``."""
    y, m, d = to_int(year), to_int(month), to_int(day)
    if not (y and m and d):
        return None
    return f"{y:04d}-{m:02d}-{d:02d}"


def to_yy_date(value: Any) -> Optional[str]:
    """``"26.09.02"`` → ``"2026-09-02"`` (해제일·등기일 형식)."""
    text = clean(value)
    if not text:
        return None
    parts = text.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return text
    yy, mm, dd = parts
    return f"20{yy}-{int(mm):02d}-{int(dd):02d}"


class Deal(BaseModel):
    """매매 한 건. 종류마다 채워지는 필드가 다르다."""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(
        default=None, description="단지·건물 이름 (단독다가구·토지는 없다)"
    )
    property_type: Optional[str] = Field(default=None, description="조회한 부동산 종류")
    house_type: Optional[str] = Field(
        default=None, description="세부 유형 (다가구, 연립, 업무 등)"
    )
    dong: Optional[str] = Field(default=None, description="법정동 이름")
    dong_code: Optional[str] = Field(
        default=None,
        description="법정동코드 뒤 5자리. 시군구코드와 합치면 get_building_register 의 지역코드",
    )
    jibun: Optional[str] = Field(default=None, description="지번 (일부는 마스킹되어 온다)")
    bun: Optional[str] = Field(
        default=None, description="본번 네 자리. get_building_register 에 그대로 넘긴다"
    )
    ji: Optional[str] = Field(default=None, description="부번 네 자리")
    road_name: Optional[str] = Field(default=None, description="도로명")
    deal_date: Optional[str] = Field(default=None, description="계약일 (YYYY-MM-DD)")
    deal_amount: Optional[int] = Field(default=None, description="거래금액 (만원)")
    exclusive_area: Optional[float] = Field(default=None, description="전용면적 (㎡)")
    total_floor_area: Optional[float] = Field(default=None, description="연면적 (㎡)")
    plottage_area: Optional[float] = Field(default=None, description="대지면적 (㎡)")
    land_area: Optional[float] = Field(default=None, description="대지권면적 (㎡)")
    building_area: Optional[float] = Field(default=None, description="건물면적 (㎡)")
    deal_area: Optional[float] = Field(default=None, description="거래면적 (㎡, 토지)")
    floor: Optional[int] = Field(default=None, description="층")
    build_year: Optional[int] = Field(default=None, description="건축년도")
    buyer: Optional[str] = Field(default=None, description="매수자 구분 (개인/법인 등)")
    seller: Optional[str] = Field(default=None, description="매도자 구분")
    dealing_type: Optional[str] = Field(default=None, description="거래유형 (중개거래/직거래)")
    agent_region: Optional[str] = Field(default=None, description="중개사 소재지")
    land_use: Optional[str] = Field(default=None, description="용도지역 (토지·상업업무용)")
    jimok: Optional[str] = Field(default=None, description="지목 (토지)")
    building_use: Optional[str] = Field(default=None, description="주용도 (상업업무용)")
    share_dealing_type: Optional[str] = Field(default=None, description="지분 거래 여부")
    registration_date: Optional[str] = Field(default=None, description="등기일자")
    cancelled: bool = Field(default=False, description="해제된 거래인지")
    cancel_date: Optional[str] = Field(default=None, description="해제 사유 발생일")

    @classmethod
    def from_api(cls, row: dict[str, Any], property_type: str) -> "Deal":
        """실거래 XML 한 행을 정규화한다."""
        return cls(
            name=clean(row.get("aptNm")) or clean(row.get("offiNm")) or clean(row.get("mhouseNm")),
            property_type=property_type,
            house_type=clean(row.get("houseType")) or clean(row.get("buildingType")),
            dong=clean(row.get("umdNm")),
            dong_code=clean(row.get("umdCd")),
            jibun=clean(row.get("jibun")),
            bun=clean(row.get("bonbun")),
            ji=clean(row.get("bubun")),
            road_name=clean(row.get("roadNm")) or clean(row.get("roadnm")),
            deal_date=to_date(row.get("dealYear"), row.get("dealMonth"), row.get("dealDay")),
            deal_amount=to_int(row.get("dealAmount")),
            exclusive_area=to_float(row.get("excluUseAr")),
            total_floor_area=to_float(row.get("totalFloorAr")),
            plottage_area=to_float(row.get("plottageAr")),
            land_area=to_float(row.get("landAr")),
            building_area=to_float(row.get("buildingAr")),
            deal_area=to_float(row.get("dealArea")),
            floor=to_int(row.get("floor")),
            build_year=to_int(row.get("buildYear")),
            buyer=clean(row.get("buyerGbn")),
            seller=clean(row.get("slerGbn")),
            dealing_type=clean(row.get("dealingGbn")),
            agent_region=clean(row.get("estateAgentSggNm")),
            land_use=clean(row.get("landUse")),
            jimok=clean(row.get("jimok")),
            building_use=clean(row.get("buildingUse")),
            share_dealing_type=clean(row.get("shareDealingType")),
            registration_date=to_yy_date(row.get("rgstDate")),
            cancelled=bool(clean(row.get("cdealType")) or clean(row.get("cdealDay"))),
            cancel_date=to_yy_date(row.get("cdealDay")),
        )


class Rent(BaseModel):
    """전월세 한 건."""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(default=None, description="단지·건물 이름 (단독다가구는 없다)")
    property_type: Optional[str] = Field(default=None, description="조회한 부동산 종류")
    house_type: Optional[str] = Field(
        default=None, description="세부 유형 (단독, 다가구, 연립 등)"
    )
    dong: Optional[str] = Field(default=None, description="법정동 이름")
    jibun: Optional[str] = Field(default=None, description="지번")
    road_name: Optional[str] = Field(default=None, description="도로명")
    deal_date: Optional[str] = Field(default=None, description="계약일 (YYYY-MM-DD)")
    rent_type: Optional[str] = Field(default=None, description="전세 / 월세 (월세금 0이면 전세)")
    deposit: Optional[int] = Field(default=None, description="보증금 (만원)")
    monthly_rent: Optional[int] = Field(default=None, description="월세 (만원, 전세면 0)")
    previous_deposit: Optional[int] = Field(default=None, description="종전 보증금 (만원)")
    previous_monthly_rent: Optional[int] = Field(default=None, description="종전 월세 (만원)")
    contract_term: Optional[str] = Field(default=None, description="계약기간 (예: 26.09~28.09)")
    contract_type: Optional[str] = Field(default=None, description="계약구분 (신규/갱신)")
    renewal_right_used: Optional[str] = Field(default=None, description="갱신요구권 사용 여부")
    exclusive_area: Optional[float] = Field(default=None, description="전용면적 (㎡)")
    total_floor_area: Optional[float] = Field(default=None, description="연면적 (㎡, 단독다가구)")
    floor: Optional[int] = Field(default=None, description="층")
    build_year: Optional[int] = Field(default=None, description="건축년도")

    @classmethod
    def from_api(cls, row: dict[str, Any], property_type: str) -> "Rent":
        """전월세 XML 한 행을 정규화한다."""
        monthly = to_int(row.get("monthlyRent"))
        return cls(
            name=clean(row.get("aptNm")) or clean(row.get("offiNm")) or clean(row.get("mhouseNm")),
            property_type=property_type,
            house_type=clean(row.get("houseType")),
            dong=clean(row.get("umdNm")),
            jibun=clean(row.get("jibun")),
            road_name=clean(row.get("roadNm")) or clean(row.get("roadnm")),
            deal_date=to_date(row.get("dealYear"), row.get("dealMonth"), row.get("dealDay")),
            rent_type=None if monthly is None else ("전세" if monthly == 0 else "월세"),
            deposit=to_int(row.get("deposit")),
            monthly_rent=monthly,
            previous_deposit=to_int(row.get("preDeposit")),
            previous_monthly_rent=to_int(row.get("preMonthlyRent")),
            contract_term=clean(row.get("contractTerm")),
            contract_type=clean(row.get("contractType")),
            renewal_right_used=clean(row.get("useRRRight")),
            exclusive_area=to_float(row.get("excluUseAr")),
            total_floor_area=to_float(row.get("totalFloorAr")),
            floor=to_int(row.get("floor")),
            build_year=to_int(row.get("buildYear")),
        )


def to_iso_date(value: Any) -> Optional[str]:
    """``"19781101"`` → ``"1978-11-01"``. 형식이 다르면 원문."""
    text = clean(value)
    if not text or len(text) != 8 or not text.isdigit():
        return text
    return f"{text[:4]}-{text[4:6]}-{text[6:]}"


def _attached_lot(row: dict[str, Any]) -> Optional[str]:
    """부속지번의 본번·부번을 ``"493-0"`` 형태로."""
    bun, ji = clean(row.get("atchBun")), clean(row.get("atchJi"))
    if not bun:
        return None
    return f"{int(bun)}-{int(ji)}" if ji else str(int(bun))


class BuildingRegister(BaseModel):
    """건축물대장 한 건. 종류(표제부/층별개요/지역지구…)마다 채워지는 필드가 다르다."""

    model_config = ConfigDict(populate_by_name=True)

    building_name: Optional[str] = Field(default=None, description="건물명")
    dong_name: Optional[str] = Field(default=None, description="동 이름")
    address: Optional[str] = Field(default=None, description="지번 주소")
    road_address: Optional[str] = Field(default=None, description="도로명 주소")
    register_kind: Optional[str] = Field(
        default=None, description="대장 종류 (일반건축물/집합건축물/전유부 등)"
    )
    register_type: Optional[str] = Field(default=None, description="대장 구분 (일반/집합)")
    main_purpose: Optional[str] = Field(default=None, description="주용도")
    etc_purpose: Optional[str] = Field(default=None, description="기타 용도")
    structure: Optional[str] = Field(default=None, description="구조")
    land_area: Optional[float] = Field(default=None, description="대지면적 (㎡)")
    building_area: Optional[float] = Field(default=None, description="건축면적 (㎡)")
    total_floor_area: Optional[float] = Field(default=None, description="연면적 (㎡)")
    building_coverage_ratio: Optional[float] = Field(default=None, description="건폐율 (%)")
    floor_area_ratio: Optional[float] = Field(default=None, description="용적률 (%)")
    ground_floors: Optional[int] = Field(default=None, description="지상 층수")
    basement_floors: Optional[int] = Field(default=None, description="지하 층수")
    household_count: Optional[int] = Field(default=None, description="세대수")
    parking_count: Optional[int] = Field(
        default=None, description="총 주차대수 (총괄표제부에만 있다)"
    )
    indoor_self_parking: Optional[int] = Field(default=None, description="옥내 자주식 주차")
    outdoor_self_parking: Optional[int] = Field(default=None, description="옥외 자주식 주차")
    indoor_mech_parking: Optional[int] = Field(default=None, description="옥내 기계식 주차")
    outdoor_mech_parking: Optional[int] = Field(default=None, description="옥외 기계식 주차")
    approval_date: Optional[str] = Field(default=None, description="사용승인일 (YYYY-MM-DD)")
    elevator_count: Optional[int] = Field(default=None, description="승용 승강기 수")
    # 층별개요
    floor_name: Optional[str] = Field(default=None, description="층 이름 (층별개요)")
    floor_type: Optional[str] = Field(default=None, description="층 구분 (지상/지하)")
    area: Optional[float] = Field(default=None, description="해당 층 면적 (㎡)")
    # 전유공용면적
    unit_name: Optional[str] = Field(default=None, description="호 이름 (예: 103호)")
    area_type: Optional[str] = Field(default=None, description="전유 / 공용 구분")
    # 주택가격
    house_price: Optional[int] = Field(default=None, description="공시가격 (원)")
    price_base_date: Optional[str] = Field(default=None, description="가격 기준일")
    # 부속지번
    attached_lot: Optional[str] = Field(default=None, description="부속 지번 (본번-부번)")
    attached_register_type: Optional[str] = Field(default=None, description="부속 대장 구분")
    # 지역지구
    zone_name: Optional[str] = Field(default=None, description="지역·지구 이름")
    zone_type: Optional[str] = Field(default=None, description="지역·지구 구분")

    @classmethod
    def from_api(cls, row: dict[str, Any]) -> "BuildingRegister":
        """건축물대장 XML 한 행을 정규화한다."""
        return cls(
            building_name=clean(row.get("bldNm")),
            dong_name=clean(row.get("dongNm")),
            address=clean(row.get("platPlc")),
            road_address=clean(row.get("newPlatPlc")),
            register_kind=clean(row.get("regstrKindCdNm")),
            register_type=clean(row.get("regstrGbCdNm")),
            main_purpose=clean(row.get("mainPurpsCdNm")),
            etc_purpose=clean(row.get("etcPurps")),
            structure=clean(row.get("strctCdNm")),
            land_area=to_float(row.get("platArea")),
            building_area=to_float(row.get("archArea")),
            total_floor_area=to_float(row.get("totArea")),
            building_coverage_ratio=to_float(row.get("bcRat")),
            floor_area_ratio=to_float(row.get("vlRat")),
            ground_floors=to_int(row.get("grndFlrCnt")),
            basement_floors=to_int(row.get("ugrndFlrCnt")),
            household_count=to_int(row.get("hhldCnt")),
            parking_count=to_int(row.get("totPkngCnt")),
            indoor_self_parking=to_int(row.get("indrAutoUtcnt")),
            outdoor_self_parking=to_int(row.get("oudrAutoUtcnt")),
            indoor_mech_parking=to_int(row.get("indrMechUtcnt")),
            outdoor_mech_parking=to_int(row.get("oudrMechUtcnt")),
            approval_date=to_iso_date(row.get("useAprDay")),
            elevator_count=to_int(row.get("rideUseElvtCnt")),
            floor_name=clean(row.get("flrNoNm")),
            floor_type=clean(row.get("flrGbCdNm")),
            area=to_float(row.get("area")),
            unit_name=clean(row.get("hoNm")),
            area_type=clean(row.get("exposPubuseGbCdNm")),
            house_price=to_int(row.get("hsprc")),
            price_base_date=to_iso_date(row.get("stdDay")),
            attached_lot=_attached_lot(row),
            attached_register_type=clean(row.get("atchRegstrGbCdNm")),
            zone_name=clean(row.get("jijiguCdNm")),
            zone_type=clean(row.get("jijiguGbCdNm")),
        )
