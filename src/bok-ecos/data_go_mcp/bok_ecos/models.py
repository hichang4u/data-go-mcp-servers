"""한국은행 ECOS 응답 모델.

필드가 ``STAT_CODE`` 처럼 대문자 스네이크로 오므로 alias 로 받아 소문자로 돌려준다.
``DATA_VALUE`` 는 문자열이라 숫자로 바꾸되, 숫자가 아니면 원문을 살린다.
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ECOS 주기 코드와 그 날짜 형식 (A/Q/M/D 는 2026-09-29 실호출로 확인, S/SM 은 문서 기준)
CYCLES = {
    "A": "년 (YYYY)",
    "S": "반기 (YYYYS1, S2)",
    "Q": "분기 (YYYYQ1~Q4)",
    "M": "월 (YYYYMM)",
    "SM": "반월 (YYYYMMS1, S2)",
    "D": "일 (YYYYMMDD)",
}


def to_number(value: Any) -> Any:
    """``"3.5"`` → ``3.5``. 숫자가 아니면 원문 그대로."""
    if not isinstance(value, str):
        return value
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


class StatTable(BaseModel):
    """통계표 한 건 (``StatisticTableList``)."""

    model_config = ConfigDict(populate_by_name=True)

    stat_code: Optional[str] = Field(default=None, alias="STAT_CODE", description="통계표 코드")
    stat_name: Optional[str] = Field(default=None, alias="STAT_NAME", description="통계표 이름")
    cycle: Optional[str] = Field(default=None, alias="CYCLE", description="주기 코드")
    parent_code: Optional[str] = Field(
        default=None, alias="P_STAT_CODE", description="상위 분류 코드"
    )
    searchable: Optional[str] = Field(
        default=None, alias="SRCH_YN", description="조회 가능 여부 (Y/N)"
    )
    org_name: Optional[str] = Field(default=None, alias="ORG_NAME", description="출처 기관")


class StatItem(BaseModel):
    """통계 세부항목 한 건 (``StatisticItemList``)."""

    model_config = ConfigDict(populate_by_name=True)

    stat_code: Optional[str] = Field(default=None, alias="STAT_CODE", description="통계표 코드")
    stat_name: Optional[str] = Field(default=None, alias="STAT_NAME", description="통계표 이름")
    item_code: Optional[str] = Field(default=None, alias="ITEM_CODE", description="항목 코드")
    item_name: Optional[str] = Field(default=None, alias="ITEM_NAME", description="항목 이름")
    group_code: Optional[str] = Field(default=None, alias="GRP_CODE", description="항목 그룹 코드")
    group_name: Optional[str] = Field(default=None, alias="GRP_NAME", description="항목 그룹 이름")
    parent_item_code: Optional[str] = Field(
        default=None, alias="P_ITEM_CODE", description="상위 항목 코드"
    )
    cycle: Optional[str] = Field(default=None, alias="CYCLE", description="주기 코드")
    start_time: Optional[str] = Field(
        default=None, alias="START_TIME", description="조회 가능 시작 시점"
    )
    end_time: Optional[str] = Field(
        default=None, alias="END_TIME", description="조회 가능 종료 시점"
    )
    data_count: Optional[int] = Field(default=None, alias="DATA_CNT", description="보유 데이터 수")
    unit_name: Optional[str] = Field(default=None, alias="UNIT_NAME", description="단위")
    weight: Optional[str] = Field(default=None, alias="WEIGHT", description="가중치")


class StatValue(BaseModel):
    """통계 값 한 건 (``StatisticSearch``)."""

    model_config = ConfigDict(populate_by_name=True)

    stat_code: Optional[str] = Field(default=None, alias="STAT_CODE", description="통계표 코드")
    stat_name: Optional[str] = Field(default=None, alias="STAT_NAME", description="통계표 이름")
    item_code1: Optional[str] = Field(default=None, alias="ITEM_CODE1", description="항목1 코드")
    item_name1: Optional[str] = Field(default=None, alias="ITEM_NAME1", description="항목1 이름")
    item_code2: Optional[str] = Field(default=None, alias="ITEM_CODE2", description="항목2 코드")
    item_name2: Optional[str] = Field(default=None, alias="ITEM_NAME2", description="항목2 이름")
    item_code3: Optional[str] = Field(default=None, alias="ITEM_CODE3", description="항목3 코드")
    item_name3: Optional[str] = Field(default=None, alias="ITEM_NAME3", description="항목3 이름")
    item_code4: Optional[str] = Field(default=None, alias="ITEM_CODE4", description="항목4 코드")
    item_name4: Optional[str] = Field(default=None, alias="ITEM_NAME4", description="항목4 이름")
    time: Optional[str] = Field(default=None, alias="TIME", description="시점")
    value: Optional[Any] = Field(default=None, alias="DATA_VALUE", description="값")
    unit_name: Optional[str] = Field(default=None, alias="UNIT_NAME", description="단위")
    weight: Optional[str] = Field(default=None, alias="WGT", description="가중치")

    @classmethod
    def from_api(cls, row: dict[str, Any]) -> "StatValue":
        """``DATA_VALUE`` 를 숫자로 바꿔 만든다."""
        return cls.model_validate({**row, "DATA_VALUE": to_number(row.get("DATA_VALUE"))})


class KeyStatistic(BaseModel):
    """100대 통계지표 한 건 (``KeyStatisticList``)."""

    model_config = ConfigDict(populate_by_name=True)

    class_name: Optional[str] = Field(default=None, alias="CLASS_NAME", description="지표 분류")
    name: Optional[str] = Field(default=None, alias="KEYSTAT_NAME", description="지표 이름")
    value: Optional[Any] = Field(default=None, alias="DATA_VALUE", description="값")
    time: Optional[str] = Field(
        default=None, alias="CYCLE", description="기준 시점 (주기 코드가 아니라 날짜)"
    )
    unit_name: Optional[str] = Field(default=None, alias="UNIT_NAME", description="단위")

    @classmethod
    def from_api(cls, row: dict[str, Any]) -> "KeyStatistic":
        """``DATA_VALUE`` 를 숫자로 바꿔 만든다."""
        return cls.model_validate({**row, "DATA_VALUE": to_number(row.get("DATA_VALUE"))})


class Term(BaseModel):
    """통계 용어 한 건 (``StatisticWord``)."""

    model_config = ConfigDict(populate_by_name=True)

    word: Optional[str] = Field(default=None, alias="WORD", description="용어")
    content: Optional[str] = Field(default=None, alias="CONTENT", description="설명")
