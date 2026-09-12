# data-go-mcp-core

`data-go-mcp.*` 서버들이 공유하는 코드. 단독으로 쓸 일은 없고 서버 패키지가 워크스페이스 소스(`[tool.uv.sources] data-go-mcp-core = { workspace = true }`)로 의존한다.

```python
from data_go_mcp.core import (
    BaseDataGoClient,
    normalize_items,
    to_camel,  # client
    DataGoAPIError,
    RESULT_CODES,  # errors
    load_api_key,  # keys: <PREFIX>_API_KEY > API_KEY
    tool_errors,
    READ_ONLY,  # tools: 예외 → ToolError, 조회 전용 annotation
    configure_logging,  # logging: stderr 전용, httpx 는 WARNING
)
```

최소 서버:

```python
class MyClient(BaseDataGoClient):
    base_url = "https://apis.data.go.kr/XXXX/Service"
    key_env_prefix = "MY_SERVER"
    default_params = {"dataType": "json"}  # XML 이면 response_format = "xml" (+ extra [xml])

    async def search(self, keyword: str) -> list[dict]:
        body = await self.get("getList", {"keyword": keyword, "numOfRows": 10})
        return normalize_items(body)


@mcp.tool(annotations=READ_ONLY)
async def search(keyword: Annotated[str, Field(description="검색어")]) -> dict:
    async with tool_errors():
        async with MyClient() as client:
            return {"items": await client.search(keyword)}
```

응답 래핑이 data.go.kr 표준(`response/header/body`)이 아니면 `_check_response(self, data) -> dict` 를 오버라이드한다. 설계 설명은 [docs/development/architecture.md](../../docs/development/architecture.md).
