"""API client for 한국은행 경제통계시스템 ECOS (https://ecos.bok.or.kr).

data.go.kr 계열이 아니다 (2026-09-29 실호출로 확인):

- 인증키가 **경로 세그먼트**다: ``/api/{서비스}/{키}/json/kr/{시작}/{끝}/{조건…}``. 쿼리스트링이 아니다
- 성공은 ``{"<서비스명>": {"list_total_count": N, "row": [...]}}``,
  실패는 ``{"RESULT": {"CODE": "INFO-100", "MESSAGE": "…"}}``
- ``INFO-200`` 은 "해당하는 데이터가 없습니다" — 오류가 아니라 빈 결과
- 통계표 이름 검색 API 가 없다. 전체 목록(844건)을 받아 이름으로 거른다 → 프로세스 안에 캐시
- ``sample`` 키는 한 번에 10건까지만 준다 (``ERROR-301``). 실제 키는 100건씩 받는다
"""

import re
from typing import Any, Optional, Sequence
from urllib.parse import quote

from data_go_mcp.core import BaseDataGoClient, DataGoAPIError

from .models import CYCLES, KeyStatistic, StatItem, StatTable, StatValue


SOURCE = "한국은행 ECOS"
NO_DATA = "INFO-200"
SAMPLE_KEY = "sample"
SAMPLE_PAGE_SIZE = 10  # sample 키 제한
PAGE_SIZE = 100
MAX_TABLE_ROWS = 2000  # 통계표 목록은 2026-09 기준 844건
MAX_ITEM_CODES = 4

# 주기별 시점 형식. A/Q/M/D 는 실호출로 확인, S/SM 은 문서 기준
TIME_FORMATS = {
    "A": re.compile(r"^\d{4}$"),
    "S": re.compile(r"^\d{4}S[12]$"),
    "Q": re.compile(r"^\d{4}Q[1-4]$"),
    "M": re.compile(r"^\d{6}$"),
    "SM": re.compile(r"^\d{6}S[12]$"),
    "D": re.compile(r"^\d{8}$"),
}

# 통계표 목록(844건)은 툴 호출마다 다시 받지 않는다. 서버는 호출마다 클라이언트를 새로 만든다
_table_cache: list[dict[str, Any]] = []


def clear_table_cache() -> None:
    """캐시한 통계표 목록을 버린다 (테스트용)."""
    _table_cache.clear()


class BokEcosAPIClient(BaseDataGoClient):
    """ECOS 클라이언트. 키가 경로에 들어가므로 요청 조립을 직접 한다."""

    base_url = "https://ecos.bok.or.kr/api"
    key_env_prefix = "BOK_ECOS"
    shared_key = False  # data.go.kr 키로는 열리지 않는다
    key_url = "https://ecos.bok.or.kr/api/"

    @property
    def page_size(self) -> int:
        """한 번에 받을 행 수. sample 키는 10건을 넘기면 ERROR-301."""
        return SAMPLE_PAGE_SIZE if self.api_key == SAMPLE_KEY else PAGE_SIZE

    # -- 요청 ----------------------------------------------------------------

    async def request(
        self, service: str, *conditions: str, start: int = 1, end: Optional[int] = None
    ) -> dict[str, Any]:
        """``/{서비스}/{키}/json/kr/{시작}/{끝}/{조건…}`` 을 호출한다."""
        end = self.page_size if end is None else end
        segments = [service, self.api_key, "json", "kr", str(start), str(end), *conditions]
        url = f"{self.base_url}/" + "/".join(quote(str(s), safe="") for s in segments)
        response = await self.http.get(url)
        response.raise_for_status()
        return self._check_response(response.json())

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """``RESULT`` 로 오는 오류를 예외로. ``INFO-200`` 은 빈 결과."""
        result = data.get("RESULT")
        if isinstance(result, dict):
            code = str(result.get("CODE", ""))
            if code == NO_DATA:
                return {"list_total_count": 0, "row": []}
            raise DataGoAPIError(code, str(result.get("MESSAGE", "")).strip(), source=SOURCE)
        body = next(iter(data.values()), {})
        return body if isinstance(body, dict) else {}

    @staticmethod
    def _page(body: dict[str, Any], items: list[Any]) -> dict[str, Any]:
        return {"items": items, "total_count": body.get("list_total_count", len(items))}

    # -- 오퍼레이션 ----------------------------------------------------------

    async def get_tables(self, stat_code: Optional[str] = None) -> dict[str, Any]:
        """통계표 목록. ``stat_code`` 를 주면 그 표(또는 하위 분류)만."""
        conditions = [stat_code] if stat_code else []
        body = await self.request("StatisticTableList", *conditions)
        rows = body.get("row") or []
        return self._page(body, [StatTable.model_validate(r).model_dump() for r in rows])

    async def find_tables(
        self, keyword: str, cycle: Optional[str] = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """통계표를 이름으로 찾는다. 검색 API 가 없어 전체 목록을 받아 거른다."""
        if not keyword or not keyword.strip():
            raise ValueError("keyword 를 지정하세요")
        self._check_cycle(cycle, allow_none=True)
        rows = await self._all_tables()
        hits = [
            r
            for r in rows
            if r.get("searchable") == "Y"
            and keyword.strip() in (r.get("stat_name") or "")
            and (cycle is None or r.get("cycle") == cycle)
        ]
        return hits[:limit]

    async def _all_tables(self) -> list[dict[str, Any]]:
        """통계표 전체 목록 (캐시)."""
        if _table_cache:
            return _table_cache
        collected: list[dict[str, Any]] = []
        start = 1
        while start <= MAX_TABLE_ROWS:
            end = start + self.page_size - 1
            body = await self.request("StatisticTableList", start=start, end=end)
            rows = body.get("row") or []
            collected += [StatTable.model_validate(r).model_dump() for r in rows]
            total = body.get("list_total_count") or 0
            if len(rows) < self.page_size or len(collected) >= total:
                break
            start = end + 1
        _table_cache.extend(collected)
        return _table_cache

    async def get_items(self, stat_code: str, num_of_rows: Optional[int] = None) -> dict[str, Any]:
        """통계 세부항목. 항목 코드와 주기별 조회 가능 기간을 준다."""
        if not stat_code or not stat_code.strip():
            raise ValueError("stat_code 를 지정하세요")
        body = await self.request("StatisticItemList", stat_code.strip(), end=num_of_rows)
        rows = body.get("row") or []
        return self._page(body, [StatItem.model_validate(r).model_dump() for r in rows])

    async def search(
        self,
        stat_code: str,
        cycle: str,
        start_time: str,
        end_time: str,
        item_codes: Optional[Sequence[Optional[str]]] = None,
        num_of_rows: Optional[int] = None,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """통계 조회. 항목 코드는 생략하면 그 통계표의 모든 항목을 준다 (최대 4개)."""
        if not stat_code or not stat_code.strip():
            raise ValueError("stat_code 를 지정하세요")
        self._check_cycle(cycle)
        self._check_time(cycle, start_time, "start_time")
        self._check_time(cycle, end_time, "end_time")
        codes = [c for c in (item_codes or []) if c]
        if len(codes) > MAX_ITEM_CODES:
            raise ValueError(
                f"항목 코드는 {MAX_ITEM_CODES}개까지 지정할 수 있습니다: {len(codes)}개"
            )

        rows_per_page = num_of_rows or self.page_size
        start = (max(page_no, 1) - 1) * rows_per_page + 1
        body = await self.request(
            "StatisticSearch",
            stat_code.strip(),
            cycle,
            start_time,
            end_time,
            *codes,
            start=start,
            end=start + rows_per_page - 1,
        )
        rows = body.get("row") or []
        return self._page(body, [StatValue.from_api(r).model_dump() for r in rows])

    async def get_key_statistics(self, num_of_rows: Optional[int] = None) -> dict[str, Any]:
        """100대 통계지표 — 환율·금리·물가 등 최신값."""
        body = await self.request("KeyStatisticList", end=num_of_rows)
        rows = body.get("row") or []
        return self._page(body, [KeyStatistic.from_api(r).model_dump() for r in rows])

    async def get_word(self, word: str, num_of_rows: Optional[int] = None) -> dict[str, Any]:
        """통계 용어 설명."""
        if not word or not word.strip():
            raise ValueError("word 를 지정하세요")
        body = await self.request("StatisticWord", word.strip(), end=num_of_rows)
        rows = body.get("row") or []
        from .models import Term

        return self._page(body, [Term.model_validate(r).model_dump() for r in rows])

    # -- 검증 ----------------------------------------------------------------

    @staticmethod
    def _check_cycle(cycle: Optional[str], *, allow_none: bool = False) -> None:
        if cycle is None and allow_none:
            return
        if cycle not in CYCLES:
            raise ValueError(f"주기는 {', '.join(CYCLES)} 중 하나여야 합니다: {cycle!r}")

    @staticmethod
    def _check_time(cycle: str, value: str, name: str) -> None:
        pattern = TIME_FORMATS[cycle]
        if not pattern.match(value or ""):
            raise ValueError(
                f"{name} 은(는) {cycle} 주기의 형식 {CYCLES[cycle]} 이어야 합니다: {value!r}"
            )
