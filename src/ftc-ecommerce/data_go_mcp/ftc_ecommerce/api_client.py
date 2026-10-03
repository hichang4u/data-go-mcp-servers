"""API client for 공정거래위원회 통신판매사업자 등록상세 제공 서비스.

2026-10-03 실호출로 확인한 것:

- 응답에 ``response`` 래핑이 없다. ``resultCode``/``items`` 가 **최상위에 바로** 온다
- 빈 값이 ``None`` 이 아니라 **``"N/A"`` 문자열**로 온다
- 실제로 거르는 파라미터는 ``brno``(사업자등록번호)와 ``prmmiMnno``(신고번호) **둘뿐**이다.
  상호 계열(``bzmnNm``, ``cmpnm``, ``entrpsNm``, ``corpNm``)은 전부 무시되어 전체
  2,758,879건이 돌아온다 → 툴에 노출하지 않고, 둘 중 하나를 반드시 받는다
- ``crno``(법인등록번호)가 들어 있어 fsc 재무제표 툴로 바로 이어진다
"""

import re
from typing import Any, Optional

from data_go_mcp.core import BaseDataGoClient, DataGoAPIError, normalize_items

from .models import OnlineSeller


DETAIL_OPERATION = "getMllBsInfoDetail_3"
MAX_ROWS = 100


def normalize_business_number(value: str) -> str:
    """``"120-88-00767"`` → ``"1208800767"``."""
    bizno = re.sub(r"\D", "", value or "")
    if len(bizno) != 10:
        raise ValueError(f"사업자번호는 숫자 10자리여야 합니다: {value!r}")
    return bizno


class FtcEcommerceAPIClient(BaseDataGoClient):
    """통신판매사업자 등록상세 API 클라이언트."""

    base_url = "https://apis.data.go.kr/1130000/MllBsDtl_3Service"
    key_env_prefix = "FTC_ECOMMERCE"
    default_params = {"resultType": "json"}

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """``response`` 래핑이 없어 최상위를 그대로 본다."""
        code = str(data.get("resultCode", ""))
        if code and code not in ("00", "0"):
            raise DataGoAPIError(code, str(data.get("resultMsg", "")))
        return data

    async def get_online_seller(
        self,
        business_number: Optional[str] = None,
        report_number: Optional[str] = None,
        num_of_rows: int = 10,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """통신판매사업자 신고 내역. 사업자번호 또는 신고번호로 조회한다."""
        params: dict[str, Any] = {
            "numOfRows": min(max(num_of_rows, 1), MAX_ROWS),
            "pageNo": max(page_no, 1),
        }
        if business_number:
            params["brno"] = normalize_business_number(business_number)
        elif report_number and report_number.strip():
            params["prmmiMnno"] = report_number.strip()
        else:
            raise ValueError(
                "사업자번호(business_number) 또는 신고번호(report_number) 중 하나는 "
                "필요합니다. 상호로는 조회할 수 없습니다 (API 가 무시합니다)"
            )

        body = await self.get(DETAIL_OPERATION, params)
        return {
            "items": [OnlineSeller.from_api(row).model_dump() for row in normalize_items(body)],
            "total_count": int(body.get("totalCount") or 0),
        }
