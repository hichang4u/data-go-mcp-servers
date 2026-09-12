"""API client for {{ cookiecutter.api_display_name }} ({{ cookiecutter.api_korean_name }})."""

from typing import Any, Optional

from data_go_mcp.core import BaseDataGoClient, normalize_items

from .models import ExampleItem


class {{ cookiecutter.api_name.replace('-', ' ').title().replace(' ', '') }}APIClient(BaseDataGoClient):
    """{{ cookiecutter.api_display_name }} API 클라이언트.

    ``BaseDataGoClient`` 가 serviceKey 주입, None 파라미터 제거, ``response/header/body`` 언래핑,
    resultCode 검사(→ ``DataGoAPIError``)를 처리한다. 여기서는 엔드포인트별 메서드만 쓴다.
    응답이 XML 이면 ``response_format = "xml"`` (+ ``data-go-mcp-core[xml]``).
    """

    base_url = "{{ cookiecutter.api_base_url }}"
    key_env_prefix = "{{ cookiecutter.api_name_underscore.upper() }}"
    default_params = {"dataType": "json"}  # API 명세에 맞게 (resultType / type / returnType ...)

    async def get_items(
        self,
        keyword: Optional[str] = None,
        page_no: int = 1,
        num_of_rows: int = 10,
    ) -> dict[str, Any]:
        """예시 조회 메서드. 엔드포인트와 파라미터명을 API 명세대로 바꾼다."""
        body = await self.get(
            "getExampleList",
            {"keyword": keyword, "pageNo": page_no, "numOfRows": num_of_rows},
        )
        return {
            "items": [ExampleItem(**item).model_dump() for item in normalize_items(body)],
            "page_no": body.get("pageNo", page_no),
            "num_of_rows": body.get("numOfRows", num_of_rows),
            "total_count": body.get("totalCount", 0),
        }
