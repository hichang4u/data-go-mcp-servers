"""API client for 국세청 사업자등록정보 진위확인 및 상태조회 (odcloud)."""

from typing import Any

from data_go_mcp.core import BaseDataGoClient, DataGoAPIError

from .models import BusinessInfo, StatusResponse, ValidateResponse


MAX_BATCH = 100


class NtsBusinessVerificationAPIClient(BaseDataGoClient):
    """국세청 사업자등록정보 API 클라이언트.

    odcloud 는 data.go.kr 표준 ``response/header/body`` 래핑이 없고
    ``{"status_code": "OK", "data": [...]}`` 형태라 ``_check_response`` 를 덮어쓴다.
    """

    base_url = "https://api.odcloud.kr/api/nts-businessman/v1"
    key_env_prefix = "NTS_BUSINESS_VERIFICATION"
    default_params = {"returnType": "JSON"}

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        status = data.get("status_code")
        if status is not None and status != "OK":
            raise DataGoAPIError(str(status), str(data.get("msg") or data.get("message") or ""))
        return data

    async def validate_business(self, businesses: list[BusinessInfo]) -> ValidateResponse:
        """사업자등록정보 진위확인 (최대 100건). 선택 필드는 빈 문자열로 보낸다."""
        if len(businesses) > MAX_BATCH:
            raise ValueError(f"Maximum {MAX_BATCH} businesses can be validated at once")
        payload = {
            "businesses": [
                {k: (v if v is not None else "") for k, v in biz.model_dump().items()}
                for biz in businesses
            ]
        }
        return ValidateResponse(**await self.post("validate", json=payload))

    async def check_status(self, business_numbers: list[str]) -> StatusResponse:
        """사업자등록 상태조회 (최대 100건). 하이픈은 제거한다."""
        if len(business_numbers) > MAX_BATCH:
            raise ValueError(f"Maximum {MAX_BATCH} business numbers can be checked at once")
        cleaned = [num.replace("-", "") for num in business_numbers]
        return StatusResponse(**await self.post("status", json={"b_no": cleaned}))
