"""API client for 고용24 채용정보 (옛 워크넷, https://www.work24.go.kr).

data.go.kr 계열이 아니다 (2026-10-01 실호출로 확인):

- data.go.kr 의 "워크넷 채용정보"는 등록유형이 **LINK** 라 공통 ``API_KEY`` 로는 열리지 않는다.
  엔드포인트가 ``www.work24.go.kr`` 이고 키는 고용24에서 **서비스별로** 따로 신청한다
- 키가 그 서비스에 신청되지 않으면 ``<GO24><error>…</error></GO24>`` 로 온다 (``wantedRoot`` 아님)
- 결과 없음은 ``<wantedRoot><message>정보가 존재하지 않습니다.</message><messageCd>006</messageCd>``.
  목록에서는 빈 결과지만 **상세에서는 그 공고가 없다는 뜻**이라 오류로 올린다
- 결과가 하나면 ``<wanted>`` 가 리스트가 아니라 **dict** 로 온다 (xmltodict). 핵심 용례인
  '회사 하나 조회'가 여기 걸리므로 직접 리스트로 만든다 (core ``normalize_items`` 는
  ``items.item`` 모양 전용이라 맞지 않는다)
- **조용히 무시되는 파라미터가 있다**: ``busiNo``(대소문자 틀림), ``regionCd``, ``empTpCd`` 를 주면
  필터가 걸리지 않고 전국 5만여 건이 그대로 온다 → 틀린 이름을 보내지 않도록 여기서 조립한다
- 지역코드는 **법정동코드 앞 5자리와 호환**이다 (``11680`` → 서울 강남구). ``11000`` 처럼 시도도 된다
- ``display`` 상한은 100 (1000 을 줘도 100건만)
- 상세 조회는 ``infoSvc`` 가 필수다. 없으면 ``messageCd 018``
"""

import re
from typing import Any, Mapping, Optional

from data_go_mcp.core import BaseDataGoClient, DataGoAPIError

from .models import CompanyProfile, JobDetail, JobPosting


SOURCE = "고용24"
NO_DATA = "006"
MAX_DISPLAY = 100
DEFAULT_INFO_SERVICE = "VALIDATION"

LIST_OPERATION = "callOpenApiSvcInfo210L01.do"
DETAIL_OPERATION = "callOpenApiSvcInfo210D01.do"

_DIGITS = re.compile(r"^\d+$")


class Work24JobsAPIClient(BaseDataGoClient):
    """고용24 채용정보 클라이언트."""

    base_url = "https://www.work24.go.kr/cm/openApi/call/wk"
    key_env_prefix = "WORK24"
    key_param = "authKey"
    shared_key = False  # data.go.kr 키로는 열리지 않는다
    key_url = "https://www.work24.go.kr (오픈API → 서비스별 신청)"
    response_format = "xml"
    default_params = {"returnType": "XML"}

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """오류 래핑이 둘이다 — ``GO24.error`` 와 ``wantedRoot.messageCd``.

        ``006``(결과 없음)은 목록에서만 빈 결과다. 상세에서는 그 공고가 없다는 뜻이므로
        여기서 묶어 처리하지 않고 호출한 쪽이 판단한다.
        """
        error = data.get("GO24")
        if isinstance(error, Mapping):
            raise DataGoAPIError("", str(error.get("error", "")).strip(), source=SOURCE)

        body = data.get("wantedRoot") or data.get("wantedDtl") or data
        if isinstance(body, Mapping) and body.get("messageCd"):
            raise DataGoAPIError(
                str(body["messageCd"]), str(body.get("message", "")).strip(), source=SOURCE
            )
        return dict(body) if isinstance(body, Mapping) else {}

    async def search_jobs(
        self,
        business_number: Optional[str] = None,
        keyword: Optional[str] = None,
        region_code: Optional[str] = None,
        occupation: Optional[str] = None,
        min_pay: Optional[int] = None,
        num_of_rows: int = 20,
        page_no: int = 1,
    ) -> dict[str, Any]:
        """채용공고 목록. 조건 없이 부르면 전국 5만여 건이므로 하나는 받아야 한다."""
        busino = re.sub(r"\D", "", business_number or "")
        if business_number and len(busino) != 10:
            raise ValueError(f"사업자등록번호는 숫자 10자리여야 합니다: {business_number!r}")
        region = normalize_region_code(region_code) if region_code else None
        if not any((busino, (keyword or "").strip(), region, occupation, min_pay)):
            raise ValueError(
                "조건을 하나는 지정하세요 (사업자번호·검색어·지역·직종·최저임금). "
                "조건이 없으면 전국 공고 전체가 조회됩니다"
            )

        try:
            body = await self.get(
                LIST_OPERATION,
                {
                    "callTp": "L",
                    "startPage": max(page_no, 1),
                    "display": min(max(num_of_rows, 1), MAX_DISPLAY),
                    "busino": busino or None,
                    "keyword": (keyword or "").strip() or None,
                    "region": region,
                    "occupation": (occupation or "").strip() or None,
                    "minPay": min_pay,
                },
            )
        except DataGoAPIError as e:
            if e.result_code != NO_DATA:  # 목록의 '결과 없음'은 오류가 아니다
                raise
            return {"items": [], "total_count": 0}
        return {
            "items": [JobPosting.from_api(r).model_dump() for r in _rows(body.get("wanted"))],
            "total_count": int(body.get("total") or 0),
        }

    async def get_job(
        self, wanted_auth_no: str, info_service: str = DEFAULT_INFO_SERVICE
    ) -> dict[str, Any]:
        """채용공고 상세. ``infoSvc`` 가 없으면 018 로 거절된다."""
        auth_no = (wanted_auth_no or "").strip()
        if not auth_no:
            raise ValueError("채용공고 번호(wanted_auth_no)를 지정하세요")
        body = await self.get(
            DETAIL_OPERATION,
            {
                "callTp": "D",
                "wantedAuthNo": auth_no,
                "infoSvc": (info_service or DEFAULT_INFO_SERVICE).strip(),
            },
        )
        company = body.get("corpInfo") or {}
        posting = body.get("wantedInfo") or {}
        return {
            "wanted_auth_no": str(body.get("wantedAuthNo") or auth_no),
            "company": CompanyProfile.from_api(dict(company)).model_dump(),
            "posting": JobDetail.from_api(dict(posting)).model_dump(),
        }


def _rows(value: Any) -> list[dict[str, Any]]:
    """결과가 하나면 dict, 여럿이면 list 로 온다 (xmltodict)."""
    if not value:
        return []
    return list(value) if isinstance(value, list) else [value]


def normalize_region_code(region_code: str) -> str:
    """법정동코드를 고용24 지역코드(앞 5자리)로. 10자리를 그대로 보내면 전국이 온다."""
    text = (region_code or "").strip()
    if not _DIGITS.match(text) or len(text) not in (5, 10):
        raise ValueError(
            f"지역코드는 법정동코드 5자리(시군구) 또는 10자리여야 합니다: {region_code!r}. "
            "nps 서버의 find_region_code 로 찾을 수 있습니다"
        )
    # molit 과 달리 시도 코드(1100000000 → 11000)도 '서울 전체'로 동작한다
    return text[:5]
