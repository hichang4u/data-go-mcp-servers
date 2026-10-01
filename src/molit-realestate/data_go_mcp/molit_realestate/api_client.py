"""API client for 국토교통부 부동산 실거래가 (https://apis.data.go.kr/1613000).

2026-09-30 실호출로 확인한 것:

- 종류별로 오퍼레이션이 따로다 (매매 7종, 전월세 4종). 토지·상업업무용·공장창고에는 전월세 API 가 없다
- 조회 조건은 법정동코드 **앞 5자리**(``LAWD_CD``)와 계약년월 ``YYYYMM``(``DEAL_YMD``) 뿐
- **잘못된 입력도 오류가 아니라 0건으로 온다** (10자리 코드, 4자리 년월, 시도 코드, 파라미터
  누락 모두 ``resultCode 000``). 그래서 보내기 전에 검증한다
- 응답은 XML. 빈 결과는 ``<items/>``
- 정상 코드가 ``00`` 이 아니라 **``000``** 이다 (core 기본 검사는 ``00`` 만 통과시킨다)
- 금액은 ``"790,000"`` 처럼 쉼표가 붙은 **만원** 단위 문자열

건축물대장(``BldRgstHubService``)도 같은 기관·같은 키다. 다만 ``SERVICETIMEOUT_ERROR``(503)를
자주 돌려주므로 재시도한다 (2026-10-01 확인: 동 전체 조회에서 특히 잦다).
"""

import asyncio
import re
from typing import Any, Mapping, Optional

from data_go_mcp.core import BaseDataGoClient, DataGoAPIError, normalize_items

from .models import BuildingRegister, Deal, Rent


# 종류 → (매매 엔드포인트, 전월세 엔드포인트). None 이면 그 API 가 없다
ENDPOINTS: dict[str, tuple[str, Optional[str]]] = {
    "아파트": (
        "RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev",
        "RTMSDataSvcAptRent/getRTMSDataSvcAptRent",
    ),
    "오피스텔": (
        "RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade",
        "RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent",
    ),
    "연립다세대": (
        "RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade",
        "RTMSDataSvcRHRent/getRTMSDataSvcRHRent",
    ),
    "단독다가구": (
        "RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade",
        "RTMSDataSvcSHRent/getRTMSDataSvcSHRent",
    ),
    "상업업무용": ("RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade", None),
    "공장창고": ("RTMSDataSvcInduTrade/getRTMSDataSvcInduTrade", None),
    "토지": ("RTMSDataSvcLandTrade/getRTMSDataSvcLandTrade", None),
}

TRADE_TYPES = list(ENDPOINTS)
RENT_TYPES = [k for k, (_, rent) in ENDPOINTS.items() if rent]

_DIGITS = re.compile(r"^\d+$")
MAX_ROWS = 1000

BUILDING_BASE = "https://apis.data.go.kr/1613000/BldRgstHubService"
# 대장 종류 → 오퍼레이션
BUILDING_KINDS = {
    "표제부": "getBrTitleInfo",
    "총괄표제부": "getBrRecapTitleInfo",
    "기본개요": "getBrBasisOulnInfo",
    "층별개요": "getBrFlrOulnInfo",
    "전유공용면적": "getBrExposPubuseAreaInfo",
    "주택가격": "getBrHsprcInfo",
    "지역지구": "getBrJijiguInfo",
    "부속지번": "getBrAtchJibunInfo",
}
# SERVICETIMEOUT 이 잦다. 3회로는 압구정동 표제부가 실패했다 (2026-10-01) — 다섯 번 본다.
BUILDING_RETRIES = 5
BUILDING_RETRY_WAIT = 0.5  # 0.5s, 1s, 2s, 4s 로 늘려 가며


class MolitRealEstateAPIClient(BaseDataGoClient):
    """실거래가 클라이언트. 종류에 따라 엔드포인트를 고른다."""

    base_url = "https://apis.data.go.kr/1613000"
    key_env_prefix = "MOLIT_REALESTATE"
    response_format = "xml"

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """정상 코드가 ``000`` 이다 (다른 data.go.kr 서비스는 ``00``)."""
        response = data.get("response")
        if not isinstance(response, Mapping):
            return data
        header = response.get("header") or {}
        code = str(header.get("resultCode", "000"))
        if code.lstrip("0") not in ("", "0"):
            raise DataGoAPIError(code, str(header.get("resultMsg", "")))
        body = response.get("body")
        return dict(body) if isinstance(body, Mapping) else {}

    async def search_trades(
        self,
        region_code: str,
        deal_ym: str,
        property_type: str = "아파트",
        num_of_rows: int = 100,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """매매 실거래. ``property_type`` 은 ``TRADE_TYPES`` 중 하나."""
        endpoint = self._endpoint(property_type, rent=False)
        body = await self._call(endpoint, region_code, deal_ym, num_of_rows, page_no)
        rows = normalize_items(body)
        return {
            "items": [Deal.from_api(r, property_type).model_dump() for r in rows],
            "total_count": int(body.get("totalCount") or 0),
        }

    async def search_rents(
        self,
        region_code: str,
        deal_ym: str,
        property_type: str = "아파트",
        num_of_rows: int = 100,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """전월세 실거래. 토지·상업업무용은 API 가 없다."""
        endpoint = self._endpoint(property_type, rent=True)
        body = await self._call(endpoint, region_code, deal_ym, num_of_rows, page_no)
        rows = normalize_items(body)
        return {
            "items": [Rent.from_api(r, property_type).model_dump() for r in rows],
            "total_count": int(body.get("totalCount") or 0),
        }

    async def get_building_register(
        self,
        region_code: str,
        bjdong_code: Optional[str] = None,
        bun: Optional[str] = None,
        ji: Optional[str] = None,
        kind: str = "표제부",
        num_of_rows: int = 50,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """건축물대장. ``region_code`` 10자리를 주면 시군구·법정동으로 쪼갠다."""
        operation = BUILDING_KINDS.get((kind or "").strip())
        if operation is None:
            raise ValueError(
                f"대장 종류는 {', '.join(BUILDING_KINDS)} 중 하나여야 합니다: {kind!r}"
            )
        sigungu, bjdong = split_region_code(region_code, bjdong_code)
        params: dict[str, Any] = {
            "sigunguCd": sigungu,
            "bjdongCd": bjdong,
            "numOfRows": min(max(num_of_rows, 1), MAX_ROWS),
            "pageNo": max(page_no, 1),
            "bun": pad_lot(bun, "본번"),
            "ji": pad_lot(ji, "부번") if ji else "0000",
        }
        body = await self._building_request(operation, params)
        rows = normalize_items(body)
        return {
            "items": [BuildingRegister.from_api(r).model_dump() for r in rows],
            "total_count": int(body.get("totalCount") or 0),
        }

    async def _building_request(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        """건축물대장 호출. SERVICETIMEOUT 은 몇 번 다시 시도한다."""
        last: DataGoAPIError | None = None
        for attempt in range(BUILDING_RETRIES):
            try:
                response = await self.http.get(
                    f"{BUILDING_BASE}/{operation}", params=self._params(params)
                )
                return self._handle(response)
            except DataGoAPIError as e:
                if "SERVICETIMEOUT" not in f"{e.result_code} {e.result_msg}".upper():
                    raise
                last = e
                if attempt < BUILDING_RETRIES - 1:
                    await asyncio.sleep(BUILDING_RETRY_WAIT * 2**attempt)
        raise DataGoAPIError(
            last.result_code if last else "",
            f"건축물대장 API 가 응답하지 않습니다 ({BUILDING_RETRIES}회 재시도). "
            "일시적인 과부하이니 잠시 후 다시 시도하세요. "
            "지번 없이 넓게 조회하면 더 자주 발생합니다",
            source=last.source if last else "data.go.kr",
        )

    # -- internals -----------------------------------------------------------

    async def _call(
        self, endpoint: str, region_code: str, deal_ym: str, num_of_rows: int, page_no: int
    ) -> dict[str, Any]:
        return await self.get(
            endpoint,
            {
                "LAWD_CD": normalize_region_code(region_code),
                "DEAL_YMD": check_deal_ym(deal_ym),
                "numOfRows": min(max(num_of_rows, 1), MAX_ROWS),
                "pageNo": max(page_no, 1),
            },
        )

    @staticmethod
    def _endpoint(property_type: str, *, rent: bool) -> str:
        pair = ENDPOINTS.get((property_type or "").strip())
        if pair is None:
            # 없는 종류를 안내하면 사용자가 그대로 다시 부른다
            choices = RENT_TYPES if rent else TRADE_TYPES
            raise ValueError(
                f"부동산 종류는 {', '.join(choices)} 중 하나여야 합니다: {property_type!r}"
            )
        endpoint = pair[1] if rent else pair[0]
        if endpoint is None:
            raise ValueError(
                f"{property_type} 은(는) 전월세 실거래 API 가 없습니다. "
                f"전월세는 {', '.join(RENT_TYPES)} 만 조회할 수 있습니다"
            )
        return endpoint


def split_region_code(region_code: str, bjdong_code: Optional[str]) -> tuple[str, str]:
    """``1168010500`` → ``("11680", "10500")``. 5자리면 법정동코드를 따로 받는다."""
    text = (region_code or "").strip()
    if _DIGITS.match(text) and len(text) == 10:
        sigungu, dong = text[:5], text[5:]
        if sigungu[2:5] == "000":
            raise ValueError(
                f"시도 단위 코드로는 조회할 수 없습니다: {region_code!r}. 시군구까지 좁히세요"
            )
        given = (bjdong_code or "").strip()
        if given and given != dong:
            raise ValueError(
                f"법정동코드가 지역코드와 다릅니다: {region_code!r} vs {bjdong_code!r}"
            )
        return sigungu, dong
    if not _DIGITS.match(text) or len(text) != 5:
        raise ValueError(
            f"지역코드는 법정동코드 5자리(시군구) 또는 10자리여야 합니다: {region_code!r}"
        )
    if text[2:5] == "000":
        raise ValueError(
            f"시도 단위 코드로는 조회할 수 없습니다: {region_code!r}. 시군구까지 좁히세요"
        )
    dong = (bjdong_code or "").strip()
    if not _DIGITS.match(dong) or len(dong) != 5:
        raise ValueError(
            f"법정동코드 5자리가 필요합니다: {bjdong_code!r}. "
            "지역코드를 10자리로 주면 자동으로 나눕니다"
        )
    return text, dong


def pad_lot(value: Optional[str], label: str) -> str:
    """``"493"`` → ``"0493"``. 건축물대장은 네 자리를 요구한다."""
    raw = (value or "").strip()
    if not raw:
        raise ValueError(f"{label}이(가) 필요합니다 (지번)")
    text = raw.lstrip("0") or "0"
    if not _DIGITS.match(text) or len(text) > 4:
        raise ValueError(f"{label}은(는) 숫자 네 자리까지입니다: {value!r}")
    return text.zfill(4)


def normalize_region_code(region_code: str) -> str:
    """법정동코드를 ``LAWD_CD``(앞 5자리)로. 10자리를 그대로 보내면 조용히 0건이 온다."""
    text = (region_code or "").strip()
    if not _DIGITS.match(text) or len(text) not in (5, 10):
        raise ValueError(
            f"지역코드는 법정동코드 5자리(시군구) 또는 10자리여야 합니다: {region_code!r}. "
            "nps 서버의 find_region_code 로 찾을 수 있습니다"
        )
    if text[2:5] == "000":  # 시도 코드(1100000000)는 앞 5자리를 잘라도 LAWD_CD 가 아니다
        raise ValueError(
            f"시도 단위 코드로는 조회할 수 없습니다: {region_code!r}. "
            "시군구 코드가 필요합니다 (예: 서울특별시가 아니라 강남구 11680)"
        )
    return text[:5]


def check_deal_ym(deal_ym: str) -> str:
    """계약년월 ``YYYYMM`` 검증. 형식이 틀려도 API 는 0건으로만 답한다."""
    text = (deal_ym or "").strip()
    if not _DIGITS.match(text) or len(text) != 6 or not 1 <= int(text[4:]) <= 12:
        raise ValueError(f"계약년월은 YYYYMM 6자리여야 합니다: {deal_ym!r}")
    return text
