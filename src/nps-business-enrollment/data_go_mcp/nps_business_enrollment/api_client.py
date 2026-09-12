"""API client for National Pension Service (국민연금공단 국민연금 가입 사업장 내역)."""

from typing import Any, Optional

from pydantic import BaseModel

from data_go_mcp.core import BaseDataGoClient, DataGoAPIError, normalize_items, to_camel

from .models import (
    INSURANCE_KINDS,
    BusinessDetailItem,
    BusinessItem,
    InsuredWorkplace,
    PeriodStatusItem,
    RegionCodeItem,
)


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


class RegionCodeAPIClient(BaseDataGoClient):
    """행정안전부 행정표준코드 법정동코드(StanReginCd) 클라이언트.

    nps 검색 파라미터(시도 2자리 / 시군구 3자리 / 읍면동 3자리)가 이 API 의
    ``sido_cd`` / ``sgg_cd`` / ``umd_cd`` 와 같아 지역명 → 코드 변환에 쓴다.
    """

    base_url = "https://apis.data.go.kr/1741000/StanReginCd"
    key_env_prefix = "NPS_BUSINESS_ENROLLMENT"
    default_params = {"type": "json"}

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """``{"StanReginCd": [{"head": [...]}, {"row": [...]}]}`` 또는 결과 없음 ``{"RESULT": …}``."""
        parts = data.get("StanReginCd")
        if not isinstance(parts, list):
            result = data.get("RESULT") or {}
            code = str(result.get("resultCode", ""))
            if code == "INFO-3":  # 데이터없음
                return {"rows": [], "total_count": 0}
            raise DataGoAPIError(code, str(result.get("resultMsg", "")))
        if not parts or not isinstance(parts[0], dict):
            raise DataGoAPIError("INVALID", "예상하지 못한 응답 형식 (StanReginCd 비어 있음)")
        head: dict[str, Any] = {}
        for entry in parts[0].get("head", []):
            head.update(entry)
        code = str((head.get("RESULT") or {}).get("resultCode", ""))
        if code != "INFO-0":
            raise DataGoAPIError(code, str((head.get("RESULT") or {}).get("resultMsg", "")))
        rows = parts[1].get("row", []) if len(parts) > 1 and isinstance(parts[1], dict) else []
        return {"rows": rows, "total_count": int(head.get("totalCount", 0))}

    async def search_region(
        self, name: str, page_no: int = 1, num_of_rows: int = 100
    ) -> dict[str, Any]:
        """지역명(부분 일치)으로 법정동코드를 조회한다."""
        body = await self.get(
            "getStanReginCdList",
            {"locatadd_nm": name, "pageNo": page_no, "numOfRows": num_of_rows},
        )
        return {
            "items": [RegionCodeItem(**row).model_dump() for row in body["rows"]],
            "page_no": page_no,
            "num_of_rows": num_of_rows,
            "total_count": body["total_count"],
        }


class InsuranceStatusAPIClient(BaseDataGoClient):
    """근로복지공단 고용·산재보험 현황정보(gySjbPstateInfoService) — XML 전용.

    사업자등록번호로 고용·산재보험 가입 사업장(상시인원, 성립일, 업종)을 조회한다.
    """

    base_url = "https://apis.data.go.kr/B490001/gySjbPstateInfoService"
    key_env_prefix = "NPS_BUSINESS_ENROLLMENT"
    response_format = "xml"

    async def get_workplaces(
        self,
        bzno: str,
        insurance: Optional[str] = None,
        page_no: int = 1,
        num_of_rows: int = 100,
    ) -> dict[str, Any]:
        """사업자등록번호(10자리)의 가입 사업장. ``insurance`` 는 "산재"/"고용"/None(둘 다)."""
        bzno = bzno.replace("-", "").strip()
        if not bzno.isdigit() or len(bzno) != 10:
            raise ValueError("사업자등록번호는 10자리 숫자여야 합니다")
        flag: Optional[str] = None
        if insurance is not None:
            codes = {name: code for code, name in INSURANCE_KINDS.items()}
            if insurance not in codes:
                raise ValueError("보험 구분은 '산재' 또는 '고용' 이어야 합니다")
            flag = codes[insurance]
        body = await self.get(
            "getGySjBoheomBsshItem",
            {
                "v_saeopjaDrno": bzno,
                "opaBoheomFg": flag,
                "pageNo": page_no,
                "numOfRows": num_of_rows,
            },
        )
        return {
            "items": [InsuredWorkplace.from_api(i).model_dump() for i in normalize_items(body)],
            "page_no": page_no,
            "num_of_rows": num_of_rows,
            "total_count": int(body.get("totalCount") or 0),
        }
