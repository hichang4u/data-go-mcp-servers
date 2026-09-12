# 아키텍처

## 저장소 구조

```
pyproject.toml            uv workspace 루트 (members = src/*). ruff/pyright/pytest 설정은 여기 하나뿐
src/
  data-go-mcp-core/       공통 패키지 (data_go_mcp.core)
  <server>/               서버당 독립 패키지 — pyproject.toml, data_go_mcp/<module>/, tests/
    data_go_mcp/<module>/
      api_client.py       BaseDataGoClient 서브클래스: 엔드포인트별 메서드 + 응답 → 모델
      models.py           pydantic 모델 (alias = API camelCase, 속성 = snake_case)
      server.py           MCPServer 인스턴스와 @mcp.tool() 함수, main()
    tests/                conftest.py(실응답 fixture) + test_api.py + test_server.py
template/                 cookiecutter 템플릿 (새 서버 골격)
tests/                    저장소 수준: stdio 스모크(test_list_tools), 실호출(test_integration)
scripts/                  check_apis.py, gen_tool_docs.py, deploy_to_pypi.py, create_mcp_server.py
```

`data_go_mcp` 는 **네임스페이스 패키지**다. `src/*/data_go_mcp/__init__.py` 를 만들면 같은 환경에 설치된 다른 서버 모듈을 import 할 수 없게 된다 (원저장소의 fsc 가 이 문제를 갖고 있었다).

## 요청 흐름

```
MCP client ──stdio──▶ server.py (MCPServer)
                         │ @mcp.tool(annotations=READ_ONLY)
                         │ async with tool_errors():
                         ▼
                      api_client.py (BaseDataGoClient 서브클래스)
                         │ self.get(endpoint, params) / self.post(...)
                         ▼
                      core.client.BaseDataGoClient
                         ├ load_api_key(prefix)        <PREFIX>_API_KEY > API_KEY
                         ├ _params(): serviceKey + default_params, None 제거
                         ├ httpx.AsyncClient (timeout 30s)
                         ├ _gateway_error(): 4xx + OpenAPI_ServiceResponse / {"code","msg"} → DataGoAPIError
                         ├ raise_for_status()
                         ├ _parse(): JSON 또는 XML(xmltodict)
                         └ _check_response(): response/header/resultCode 검사 → body 반환 (훅)
                         ▼
                      normalize_items(body) → pydantic 모델 → dict
                         ▼
                      tool_errors: DataGoAPIError / httpx.HTTPError / ValueError → ToolError
                         ▼
MCP client ◀── CallToolResult(is_error=True, "data.go.kr 오류 [30] …") 또는 정상 결과
```

## core 패키지 (`data_go_mcp.core`)

| 모듈 | 제공 | 비고 |
|---|---|---|
| `keys` | `load_api_key(prefix, explicit=None)` | 우선순위: 인자 > `<PREFIX>_API_KEY` > `API_KEY`. 없으면 `ValueError` |
| `errors` | `DataGoAPIError(result_code, result_msg)`, `RESULT_CODES` | `str()` 은 `[30] MSG (등록되지 않은 서비스키)` 형태 |
| `client` | `BaseDataGoClient`, `to_camel`, `normalize_items` | 아래 계약 참조 |
| `xml` | `parse_xml_response(text)` | extra `xml` (xmltodict). 빈 요소는 `None` |
| `tools` | `tool_errors()`, `READ_ONLY` | 툴 본문을 감싸는 async context manager / `ToolAnnotations(read_only_hint, open_world_hint)` |
| `logging` | `configure_logging(name)` | stderr 핸들러 1개, httpx/httpcore 는 WARNING (URL 의 serviceKey 가 로그에 남지 않도록) |

### `BaseDataGoClient` 계약

```python
class NPSAPIClient(BaseDataGoClient):
    base_url = "https://apis.data.go.kr/B552015/NpsBplcInfoInqireServiceV2"
    key_env_prefix = "NPS_BUSINESS_ENROLLMENT"   # <PREFIX>_API_KEY
    default_params = {"dataType": "json"}        # 모든 요청에 붙는 파라미터
    response_format = "json"                     # 또는 "xml"
    key_param = "serviceKey"                     # 키 파라미터 이름
```

- `await self.get(endpoint, params)` / `await self.post(endpoint, json=, params=)` → 언래핑된 body(dict)
- 응답 래핑이 표준(`response/header/body`)이 아니면 `_check_response(self, data) -> dict` 를 오버라이드한다.
  odcloud(nts, presidential)는 `{"status_code": "OK", "data": [...]}` 형태라 여기서 검사한다.
- `normalize_items(body)` 는 `items.item` 이 리스트/단일/빈 문자열/`items` 자체가 리스트인 경우를 모두 리스트로 만든다.

### API 계열별 차이

| 계열 | 서버 | 키 전달 | 형식 파라미터 | 응답 래핑 | 비고 |
|---|---|---|---|---|---|
| data.go.kr 표준 | nps, pps, fsc | `serviceKey` 쿼리 | `dataType=json` / `type=json` / `resultType=json` | `response.header.resultCode` + `response.body` | 미신청 시 HTTP 403 + `OpenAPI_ServiceResponse` |
| odcloud | nts, presidential | `serviceKey` 쿼리 | `returnType=JSON` | `status_code`/`data` (nts), `currentCount`/`data` (presidential) | 미신청 시 HTTP 401 + `{"code":-401}`. presidential 은 `cond[컬럼::EQ\|LIKE]` 서버 필터 |
| KOSHA | msds | `serviceKey` 쿼리 | 없음 (XML 전용) | data.go.kr 표준과 동일 | data.go.kr 키 그대로 사용 가능 |

## 에러 규약

- 클라이언트 계층은 **예외를 던진다**: `DataGoAPIError`(API 가 오류 코드), `httpx.HTTPStatusError`/`httpx.HTTPError`(전송), `ValueError`(입력 검증, pydantic 포함).
- 툴 계층은 `async with tool_errors():` 로 감싸 `ToolError` 로 바꾼다. MCPServer 가 이를 `CallToolResult(is_error=True)` 로 만든다.
- 툴은 `{"error": ...}` 같은 dict 를 **돌려주지 않는다**. LLM 이 실패를 정상 결과로 읽는 것을 막기 위해서다.
- "결과 없음"은 오류가 아니다 (빈 `items`, "조회된 … 없습니다" 텍스트).

## 툴 정의 규약

```python
@mcp.tool(annotations=READ_ONLY)
async def search_business(
    wkpl_nm: Annotated[Optional[str], Field(description="사업장명 (부분 일치)")] = None,
    page_no: Annotated[int, Field(description="페이지 번호 (기본값: 1)")] = 1,
) -> dict[str, Any]:
    """사업장 정보를 조회합니다. Search business enrollment. Returns items, total_count, ..."""
```

- 파라미터 설명은 반드시 `Field(description=)` 에. MCPServer 는 docstring 의 `Args:` 절을 스키마에 싣지 않는다.
- docstring 첫 줄은 한/영 병기, 반환 구조를 한 줄로.
- 이 저장소의 툴은 전부 조회이므로 `READ_ONLY` (`readOnlyHint=True, openWorldHint=True`).
- `main()` 은 `configure_logging()` → 키 존재 경고(stderr) → `mcp.run()`. stdout 에는 아무것도 쓰지 않는다.

## mcp SDK 2.x 메모

| 1.x | 2.x |
|---|---|
| `from mcp.server.fastmcp import FastMCP` | `from mcp.server.mcpserver import MCPServer` |
| 저수준 `@server.list_tools()` 데코레이터 | 제거됨 (생성자 `on_list_tools=`) — 이 저장소는 쓰지 않는다 |
| `CallToolResult.isError`, `Tool.inputSchema` | `is_error`, `input_schema` (snake_case) |
| — | `mcp.Client(server)` 로 인프로세스 테스트, `ToolError` 는 `mcp.server.mcpserver.exceptions` |

설계 배경과 결정 이력은 [PRD.md](PRD.md), 작업 기록은 [PLAN.md](PLAN.md).
