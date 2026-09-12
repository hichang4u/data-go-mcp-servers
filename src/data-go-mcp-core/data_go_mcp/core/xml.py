"""XML 응답을 JSON 응답과 같은 dict 형태로 변환한다 (extra ``xml`` 필요)."""

from typing import Any


def parse_xml_response(text: str) -> dict[str, Any]:
    """``<response><header/><body/></response>`` 를 ``{"response": {...}}`` 로.

    값은 전부 문자열(또는 빈 요소는 ``None``)로 남는다 — 숫자 변환은 호출 측 Pydantic 모델 몫.
    """
    try:
        import xmltodict
    except ImportError as e:  # pragma: no cover
        raise ImportError("XML 응답을 다루려면 data-go-mcp-core[xml] 을 설치하세요") from e

    try:
        data = xmltodict.parse(text)
    except Exception as e:
        raise ValueError(f"Failed to parse XML response: {e}") from e
    return data if isinstance(data, dict) else {}
