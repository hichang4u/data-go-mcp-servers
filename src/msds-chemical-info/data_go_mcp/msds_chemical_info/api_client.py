"""API client for 안전보건공단 물질안전보건자료(MSDS) — XML 전용, data.go.kr 키로 호출 가능."""

import asyncio
from typing import Any, Iterable

from data_go_mcp.core import BaseDataGoClient, normalize_items

from .models import (
    SECTION_TITLES,
    ChemicalListItem,
    ChemicalListResponse,
    MsdsDetailItem,
    MsdsSection,
    SearchType,
)


def _drop_empty(item: dict[str, Any]) -> dict[str, Any]:
    """Xmltodict 는 빈 요소(<casNo/>)를 None 으로 준다 — 모델 기본값이 쓰이도록 뺀다."""
    return {k: v for k, v in item.items() if v is not None}


def detect_search_type(term: str) -> SearchType:
    """검색어 형태로 검색 구분을 추정한다. 모호하면 국문명."""
    t = term.strip()
    upper = t.upper()
    if upper.startswith("UN") and upper[2:].isdigit():
        return SearchType.UN_NO
    if t.isdigit() and len(t) == 4:
        return SearchType.UN_NO
    if upper.startswith("KE-"):
        return SearchType.KE_NO
    parts = t.split("-")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        # EN No.: 3-3-1 (예: 200-753-7) / CAS No.: 2~7-2-1 (예: 71-43-2)
        if len(parts[0]) == 3 and len(parts[1]) == 3 and len(parts[2]) <= 2:
            return SearchType.EN_NO
        if 2 <= len(parts[0]) <= 7 and len(parts[1]) == 2 and len(parts[2]) == 1:
            return SearchType.CAS_NO
    return SearchType.KOREAN_NAME


class MsdsChemicalInfoAPIClient(BaseDataGoClient):
    """KOSHA MSDS API 클라이언트. 응답은 XML → core 가 dict 로 바꿔 준다."""

    base_url = "https://msds.kosha.or.kr/openapi/service/msdschem"
    key_env_prefix = "MSDS_CHEMICAL_INFO"
    response_format = "xml"

    async def search_chemicals(
        self,
        search_word: str,
        search_type: SearchType = SearchType.KOREAN_NAME,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> ChemicalListResponse:
        """화학물질 목록 검색 (chemlist)."""
        body = await self.get(
            "chemlist",
            {
                "searchWrd": search_word,
                "searchCnd": int(search_type),
                "pageNo": page_no,
                "numOfRows": num_of_rows,
            },
        )
        return ChemicalListResponse(
            items=[ChemicalListItem(**_drop_empty(item)) for item in normalize_items(body)],
            totalCount=int(body.get("totalCount") or 0),
            pageNo=int(body.get("pageNo") or page_no),
            numOfRows=int(body.get("numOfRows") or num_of_rows),
        )

    async def get_chemical_detail(self, chem_id: str, section_number: int) -> MsdsSection:
        """MSDS 섹션 하나 조회 (chemdetail01 ~ chemdetail16)."""
        if not 1 <= section_number <= 16:
            raise ValueError(
                f"Invalid section number: {section_number}. Must be between 1 and 16."
            )
        body = await self.get(f"chemdetail{section_number:02d}", {"chemId": chem_id})
        return MsdsSection(
            section_number=section_number,
            section_title=SECTION_TITLES[section_number],
            items=[MsdsDetailItem(**_drop_empty(item)) for item in normalize_items(body)],
        )

    async def get_sections(
        self, chem_id: str, numbers: Iterable[int], *, tolerate_errors: bool = False
    ) -> dict[int, MsdsSection]:
        """여러 섹션을 동시에 조회. ``tolerate_errors`` 면 실패한 섹션은 빈 섹션 + error 로."""
        nums = list(numbers)
        results: list[Any] = await asyncio.gather(
            *(self.get_chemical_detail(chem_id, n) for n in nums),
            return_exceptions=tolerate_errors,
        )
        sections: dict[int, MsdsSection] = {}
        for n, result in zip(nums, results):
            if isinstance(result, BaseException):
                sections[n] = MsdsSection(
                    section_number=n, section_title=SECTION_TITLES[n], items=[], error=str(result)
                )
            else:
                sections[n] = result
        return sections
