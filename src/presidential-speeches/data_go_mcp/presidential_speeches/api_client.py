"""API client for 대통령기록관 대통령연설기록(연설문) — odcloud 파일데이터 API."""

from typing import Any, Optional

from data_go_mcp.core import BaseDataGoClient, DataGoAPIError

from .models import SpeechesResponse2022, SpeechesResponse2023


UDDI_2023 = "uddi:f30c6ace-297a-4a9e-9229-844153ed21ba"  # 2023-09-12 갱신본 (연설연도)
UDDI_2022 = "uddi:1c8b5454-bd4e-45db-98f7-fe94d71f271b"  # 이전 본 (연설일자 포함)


class PresidentialSpeechesAPIClient(BaseDataGoClient):
    """대통령 연설문 API 클라이언트.

    odcloud 는 ``{"page","perPage","totalCount","currentCount","matchCount","data"}`` 형태이며
    ``cond[컬럼::EQ|LIKE]=값`` 쿼리로 서버측 필터를 지원한다.
    """

    base_url = "https://api.odcloud.kr/api/15084167/v1"
    key_env_prefix = "PRESIDENTIAL_SPEECHES"
    default_params = {"returnType": "json"}

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        if "data" not in data:
            raise DataGoAPIError(
                str(data.get("code", "")), str(data.get("msg", "unexpected response"))
            )
        return data

    async def get_speeches_2023(
        self, page: int = 1, per_page: int = 10, **cond: Any
    ) -> SpeechesResponse2023:
        """2023 버전 목록 (연설연도). ``cond`` 는 이미 ``cond[...]`` 형태의 키."""
        body = await self.get(UDDI_2023, {"page": page, "perPage": per_page, **cond})
        return SpeechesResponse2023(**body)

    async def get_speeches_2022(
        self, page: int = 1, per_page: int = 10, **cond: Any
    ) -> SpeechesResponse2022:
        """2022 버전 목록 (연설일자)."""
        body = await self.get(UDDI_2022, {"page": page, "perPage": per_page, **cond})
        return SpeechesResponse2022(**body)

    @staticmethod
    def build_cond(
        president: Optional[str] = None,
        title: Optional[str] = None,
        year: Optional[int] = None,
        location: Optional[str] = None,
        use_2023_version: bool = True,
    ) -> dict[str, Any]:
        """검색 조건을 odcloud ``cond[]`` 파라미터로."""
        cond: dict[str, Any] = {}
        if president:
            cond["cond[대통령::EQ]"] = president
        if title:
            cond["cond[글제목::LIKE]"] = title
        if year:
            if use_2023_version:
                cond["cond[연설연도::EQ]"] = year
            else:
                cond["cond[연설일자::LIKE]"] = str(year)
        if location:
            cond["cond[연설장소::LIKE]"] = location
        return cond

    async def search_speeches(
        self,
        president: Optional[str] = None,
        title: Optional[str] = None,
        year: Optional[int] = None,
        location: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
        use_2023_version: bool = True,
    ) -> SpeechesResponse2023 | SpeechesResponse2022:
        """서버측 필터로 연설문 검색. ``match_count`` 가 조건에 맞는 전체 건수."""
        cond = self.build_cond(president, title, year, location, use_2023_version)
        if use_2023_version:
            return await self.get_speeches_2023(page, per_page, **cond)
        return await self.get_speeches_2022(page, per_page, **cond)
