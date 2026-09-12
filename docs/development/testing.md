# 테스트

## 명령

```bash
uv run pytest                    # 전체 (integration 마커는 API_KEY 없으면 skip)
uv run pytest -m integration     # 실호출 — 루트 .env 의 API_KEY 를 conftest 가 읽는다
uv run pytest src/nps-business-enrollment/tests -q
uv run pytest tests/test_list_tools.py       # 6개 서버를 실제 stdio 서브프로세스로 띄워 list_tools
```

설정은 루트 `pyproject.toml` 하나다 (`asyncio_mode = "auto"`, `--import-mode=importlib`, `testpaths = ["tests", "src/*/tests"]`). **서버별 `pyproject.toml` 에 `[tool.pytest.ini_options]` 를 두지 않는다** — 그 디렉터리에서 실행하면 루트 설정이 가려진다.

`src/*/tests/` 에 `__init__.py` 를 두지 않는다. 세 곳 이상에 `tests` 패키지가 있으면 importlib 모드에서 모듈 이름이 충돌해 다른 서버의 테스트가 중복 수집된다. 파일 간 공유는 `conftest.py` fixture 로.

## 규칙

1. **테스트 먼저.** 새 기능·수정은 실패하는 테스트를 보고 나서 구현한다 (superpowers `test-driven-development`).
2. **HTTP 는 `respx`** 로만 가로챈다. `AsyncMock` 으로 클라이언트 메서드를 통째로 바꾸지 않는다 — 그러면 파라미터 이름·응답 파싱을 검증하지 못한다.
3. **fixture 는 실응답.** `conftest.py` 의 샘플은 실제 API 가 돌려준 JSON/XML 을 줄인 것이다. 지어내지 않는다.
4. **툴은 인프로세스 `mcp.Client(mcp)` 로 호출**한다. `isError` 경로까지 클라이언트가 보는 그대로 검증된다.

## 패턴

### 클라이언트 (test_api.py)

```python
@respx.mock
async def test_search_sends_camel_case_params(base_url, search_response):
    route = respx.get(f"{base_url}/getBassInfoSearchV2").mock(
        return_value=httpx.Response(200, json=search_response)
    )
    async with NPSAPIClient() as client:
        result = await client.search_business(wkpl_nm="삼성전자", bzowr_rgst_no=None)

    q = route.calls.last.request.url.params      # 보낸 쿼리 검증
    assert q["serviceKey"] == "test-key"
    assert q["wkplNm"] == "삼성전자"
    assert "bzowrRgstNo" not in q                # None 은 빠져야 한다
    assert result["items"][0]["wkpl_nm"] == "…"  # 파싱 검증
```

오류 경로: `resultCode != "00"` → `pytest.raises(DataGoAPIError)`; HTTP 5xx → `httpx.HTTPStatusError`.

### 툴 (test_server.py)

```python
async def test_all_tools_are_read_only_with_described_params():
    for tool in await mcp.list_tools():
        assert tool.annotations.read_only_hint is True
        for name, prop in tool.input_schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name}"

@respx.mock
async def test_api_error_is_reported_as_tool_error(base_url):
    respx.get(...).mock(return_value=httpx.Response(200, json={"response": {"header": {"resultCode": "30", ...}}}))
    async with Client(mcp) as client:
        result = await client.call_tool("search_business", {"wkpl_nm": "x"})
    assert result.is_error is True
    assert "[30]" in result.content[0].text
```

`_text(result)` 헬퍼로 `TextContent` 를 꺼내고, dict 반환 툴은 `json.loads` 한다.

### 키 없는 경우

`monkeypatch.delenv("API_KEY")` 후 툴을 부르면 `is_error=True` 에 "API_KEY" 가 포함돼야 한다. 서버 기동 자체는 키 없이도 된다 (`tests/test_list_tools.py::test_server_starts_without_api_key`).

### 실호출 (integration)

`tests/test_integration.py` — 서버당 툴 1회. 루트 `tests/conftest.py` 가 `.env` 를 로드하고 `API_KEY` 가 없으면 `integration` 마커를 skip 한다. CI 에는 키가 없으므로 hermetic.

## 품질 게이트 (CI 필수)

```bash
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
uv run pyright src scripts tests
```

`uv run pre-commit install` 해 두면 커밋마다 돈다. pydantic 필드 기본값은 `Field(default=None, …)` 로 — 위치 인자 `Field(None, …)` 는 pyright 가 필수 인자로 본다.
