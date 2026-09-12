"""data.go.kr 계열 API 공통 HTTP 클라이언트.

서버별 ``api_client.py`` 는 이 클래스를 상속해 ``base_url`` / ``key_env_prefix`` /
``default_params`` 만 지정하고, 엔드포인트별 메서드에서 ``get`` / ``post`` 를 호출한다.
응답 래핑이 표준(``response/header/body``)과 다른 API(odcloud 등)는 ``_check_response`` 를
오버라이드한다.
"""

from typing import Any, ClassVar, Literal, Mapping

import httpx

from .errors import DataGoAPIError
from .keys import load_api_key


def to_camel(snake: str) -> str:
    """``ldong_addr_mgpl_dg_cd`` → ``ldongAddrMgplDgCd``."""
    head, *rest = snake.split("_")
    return head + "".join(part.title() for part in rest)


def normalize_items(body: Mapping[str, Any]) -> list[dict[str, Any]]:
    """``body.items`` 를 항상 리스트로 돌려준다.

    data.go.kr 응답은 결과 수에 따라 ``items.item`` 이 리스트/단일 객체/빈 문자열로 바뀌고,
    일부 서비스(나라장터)는 ``items`` 자체가 리스트다.
    """
    items = body.get("items")
    if not items:
        return []
    if isinstance(items, list):
        return items
    item = items.get("item") if isinstance(items, Mapping) else None
    if not item:
        return []
    return item if isinstance(item, list) else [item]


class BaseDataGoClient:
    """공통 클라이언트. 서브클래스에서 클래스 속성을 채운다."""

    base_url: ClassVar[str] = ""
    key_env_prefix: ClassVar[str] = ""
    key_param: ClassVar[str] = "serviceKey"
    default_params: ClassVar[Mapping[str, Any]] = {}
    response_format: ClassVar[Literal["json", "xml"]] = "json"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout: float = 30.0,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = load_api_key(self.key_env_prefix, explicit=api_key)
        self.http = http or httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def close(self) -> None:
        """HTTP 연결을 닫는다."""
        await self.http.aclose()

    # -- public ---------------------------------------------------------------

    async def get(self, endpoint: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """GET 요청. ``None`` 값 파라미터는 제거하고 키·기본 파라미터를 주입한다."""
        response = await self.http.get(self._url(endpoint), params=self._params(params))
        return self._handle(response)

    async def post(
        self,
        endpoint: str,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """POST 요청. 키는 쿼리스트링, 본문은 JSON."""
        response = await self.http.post(
            self._url(endpoint), params=self._params(params), json=json
        )
        return self._handle(response)

    # -- hooks ----------------------------------------------------------------

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """파싱된 응답을 검사하고 유용한 부분을 돌려준다. 기본은 data.go.kr 표준 형태."""
        response = data.get("response")
        if not isinstance(response, Mapping):
            return data
        header = response.get("header") or {}
        code = str(header.get("resultCode", "00"))
        if code != "00":
            raise DataGoAPIError(code, str(header.get("resultMsg", "")))
        body = response.get("body")
        return dict(body) if isinstance(body, Mapping) else {}

    # -- internals ------------------------------------------------------------

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def _params(self, params: Mapping[str, Any] | None) -> dict[str, Any]:
        merged: dict[str, Any] = {self.key_param: self.api_key, **self.default_params}
        for key, value in (params or {}).items():
            if value is not None:
                merged[key] = value
        return merged

    def _parse(self, response: httpx.Response) -> dict[str, Any]:
        if self.response_format == "xml":
            from .xml import parse_xml_response

            return parse_xml_response(response.text)
        return response.json()

    def _handle(self, response: httpx.Response) -> dict[str, Any]:
        gateway_error = self._gateway_error(response)
        if gateway_error is not None:
            raise gateway_error
        response.raise_for_status()
        return self._check_response(self._parse(response))

    def _gateway_error(self, response: httpx.Response) -> DataGoAPIError | None:
        """게이트웨이 오류(활용신청 전 등)를 DataGoAPIError 로.

        data.go.kr(JSON/XML ``OpenAPI_ServiceResponse``) 과 odcloud(``{"code","msg"}``) 형태 모두 처리.
        XML 서비스는 게이트웨이 오류도 XML 로, 때로는 HTTP 200 으로 온다.
        """
        data: Any = None
        try:
            data = response.json()
        except ValueError:
            if self.response_format == "xml" and "OpenAPI_ServiceResponse" in response.text[:200]:
                from .xml import parse_xml_response

                try:
                    data = parse_xml_response(response.text)
                except ValueError:
                    return None
        if not isinstance(data, Mapping):
            return None
        header = (data.get("OpenAPI_ServiceResponse") or {}).get("cmmMsgHeader")
        if header:
            return DataGoAPIError(
                str(header.get("returnReasonCode", "")),
                f"{header.get('errMsg', '')} ({header.get('returnAuthMsg', '')})",
            )
        # odcloud 계열: HTTP 4xx + {"code": -401, "msg": "..."}
        if response.is_error and "code" in data and "msg" in data:
            return DataGoAPIError(str(data["code"]), str(data["msg"]))
        return None
