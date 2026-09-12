"""API client for National Pension Service (국민연금공단 국민연금 가입 사업장 내역)."""

from typing import Any, Optional

from pydantic import BaseModel

from data_go_mcp.core import BaseDataGoClient, normalize_items, to_camel

from .models import BusinessDetailItem, BusinessItem, PeriodStatusItem


class NPSAPIClient(BaseDataGoClient):
    """국민연금공단 API 클라이언트."""

    base_url = "https://apis.data.go.kr/B552015/NpsBplcInfoInqireServiceV2"
    key_env_prefix = "NPS_BUSINESS_ENROLLMENT"
    default_params = {"dataType": "json"}

    async def _search(
        self, endpoint: str, model: type[BaseModel], params: dict[str, Any]
    ) -> dict[str, Any]:
        """snake_case 파라미터를 camelCase로 바꿔 호출하고 items를 모델로 파싱한다."""
        body = await self.get(endpoint, {to_camel(k): v for k, v in params.items()})
        items: list[dict[str, Any]] = []
        for raw in normalize_items(body):
            try:
                items.append(model(**raw).model_dump())
            except Exception:
                # 모델에 없는 필드가 오더라도 원본을 버리지 않는다
                items.append(raw)
        return {
            "items": items,
            "page_no": body.get("pageNo", params.get("page_no")),
            "num_of_rows": body.get("numOfRows", params.get("num_of_rows")),
            "total_count": body.get("totalCount", 0),
        }

    async def search_business(
        self,
        ldong_addr_mgpl_dg_cd: Optional[str] = None,
        ldong_addr_mgpl_sggu_cd: Optional[str] = None,
        ldong_addr_mgpl_sggu_emd_cd: Optional[str] = None,
        wkpl_nm: Optional[str] = None,
        bzowr_rgst_no: Optional[str] = None,
        page_no: int = 1,
        num_of_rows: int = 100,
    ) -> dict[str, Any]:
        """사업장 정보조회 — 기본 100개 반환 (최대 100개)."""
        return await self._search(
            "getBassInfoSearchV2",
            BusinessItem,
            {
                "ldong_addr_mgpl_dg_cd": ldong_addr_mgpl_dg_cd,
                "ldong_addr_mgpl_sggu_cd": ldong_addr_mgpl_sggu_cd,
                "ldong_addr_mgpl_sggu_emd_cd": ldong_addr_mgpl_sggu_emd_cd,
                "wkpl_nm": wkpl_nm,
                "bzowr_rgst_no": bzowr_rgst_no,
                "page_no": page_no,
                "num_of_rows": num_of_rows,
            },
        )

    async def get_business_detail(
        self, seq: int, page_no: int = 1, num_of_rows: int = 10
    ) -> dict[str, Any]:
        """사업장 상세정보 조회."""
        return await self._search(
            "getDetailInfoSearchV2",
            BusinessDetailItem,
            {"seq": seq, "page_no": page_no, "num_of_rows": num_of_rows},
        )

    async def get_period_status(
        self,
        seq: int,
        data_crt_ym: Optional[str] = None,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> dict[str, Any]:
        """기간별 현황 정보조회."""
        return await self._search(
            "getPdAcctoSttusInfoSearchV2",
            PeriodStatusItem,
            {
                "seq": seq,
                "data_crt_ym": data_crt_ym,
                "page_no": page_no,
                "num_of_rows": num_of_rows,
            },
        )
