# CLAUDE.md

data.go.kr 공공 API 10종(서버 6개)을 MCP 서버로 제공하는 uv 워크스페이스. Python 3.10+, `mcp>=2.2,<3`.

## 명령

```bash
uv sync --dev --all-packages                     # 최초/의존성 변경 후
uv run pytest                                    # 전체. integration 마커는 .env 의 API_KEY 없으면 skip
uv run pytest src/<server>/tests -q              # 서버 하나
uv run pytest -m integration                     # 실호출 (키 필요)
uv run ruff check src scripts tests && uv run ruff format --check src scripts tests
uv run pyright src scripts tests
uv run python scripts/check_apis.py              # 10개 API 생존·권한
uv run python scripts/gen_tool_docs.py [--check] # 툴 레퍼런스 문서 재생성
uv run python -m data_go_mcp.<module>.server     # 서버 단독 실행 (stdio)
```

Windows 에서 `uv` 가 PATH 에 없으면 `python -m uv …`. 이 셸에서 이모지 출력은 `PYTHONIOENCODING=utf-8`.

## 구조

- `src/data-go-mcp-core` — 공통: `BaseDataGoClient`, `DataGoAPIError`, `load_api_key`, `tool_errors`, `READ_ONLY`, `configure_logging`
- `src/<server>/data_go_mcp/<module>/{api_client,models,server}.py` + `tests/{conftest,test_api,test_server}.py`. 서버가 API 여러 개를 쓰면 `api_client.py` 에 클라이언트 클래스 여러 개(같은 `key_env_prefix`), 테스트는 `test_<api>_api.py` (nps 3종, fsc 3종)
- `tests/` — stdio 스모크(`test_list_tools`), 실호출(`test_integration`), 루트 `conftest.py`(.env 로드, integration skip)
- `template/` — cookiecutter. `docs/development/` — 설계·계획. `docs/guide/` — 사용자 문서.

상세: [docs/development/architecture.md](docs/development/architecture.md). 새 API: [docs/development/adding-a-server.md](docs/development/adding-a-server.md) — 기존 서버의 주제면 그 서버에 툴을 추가하고(설정 항목을 늘리지 않기 위해), 아니면 새 서버.

## 반드시 지킬 것

- **테스트 먼저.** 실패를 확인한 뒤 구현. HTTP 는 `respx`, 툴은 `mcp.Client(mcp)` 인프로세스 호출, fixture 는 실응답.
- 툴은 `@mcp.tool(annotations=READ_ONLY)` + 모든 파라미터 `Field(description=)` + `async with tool_errors():`. dict 로 오류 반환 금지. docstring `Args:` 는 스키마에 안 실린다.
- 클라이언트는 `BaseDataGoClient` 상속, 예외로 실패를 알린다. 래핑이 다르면 `_check_response` 오버라이드.
- `data_go_mcp/__init__.py` 금지 (네임스페이스). `src/*/tests/__init__.py` 금지 (importlib 충돌). 서버별 pyproject 에 pytest/ruff 설정 금지.
- pydantic `Field(default=None, …)`. `Field(None, …)` 는 pyright 오류.
- stdout 에 `print()` 금지 (프로토콜 채널). 로그는 `configure_logging` → stderr.
- 환경변수: `API_KEY` 공통, `<SERVER>_API_KEY` 서버별 우선. 키를 커밋·로그·fixture 에 넣지 않는다.
- mcp 2.x: `MCPServer`, `CallToolResult.is_error`, `Tool.input_schema` (snake_case). `FastMCP`·저수준 `@server.list_tools()` 는 없다.
- 커밋: Conventional Commits, 태스크 단위. 작업은 브랜치(`sN-…`)에서, 스프린트 끝에 `/code-review` → 수정(테스트 먼저) → `main` merge → push.
- 문서 갱신: 툴 시그니처 변경 시 `gen_tool_docs.py`; 진행 기록은 `docs/development/PLAN.md`; 사용자 문서에 내부 용어(S2, D4, FR-3) 금지.

## 함정 (한 번씩 겪은 것)

- 여러 서버가 같은 `tests/test_api.py` basename 을 쓴다 → 루트 pytest 는 `--import-mode=importlib`.
- ruff `--fix` 가 `Optional[X]` 를 `X | None` 로 바꾼다. 그 뒤에 문자열 치환을 하면 놓친다.
- `sed`/heredoc 으로 긴 파일을 쓰면 Bash 명령이 잘릴 수 있다 → 큰 파일은 Write 도구로.
- Windows cp949 콘솔에서 이모지 `print()` 는 `UnicodeEncodeError` → 스크립트 상단 `sys.stdout.reconfigure(encoding="utf-8")`.
- `.env` 는 서버(`load_dotenv`)와 루트 conftest 가 읽는다. 키 없는 경로를 테스트할 땐 `cwd=tmp_path` 또는 `monkeypatch.delenv`.
- 엔드포인트는 활용신청 승인 페이지의 End Point 를 그대로 (주식시세는 `/1160100/GetStockSecuritiesInfoService_V2/…`, `service/` 없음). 문서의 파라미터가 무시되기도 한다(주식시세 `crno`) → 실호출로 확인.
- fixture dict 는 모듈 상수를 공유한다. 테스트 안에서 고치려면 깊은 복사 먼저.
- XML 서비스는 게이트웨이 오류도 XML 로, 200 으로 올 때도 있다 → core `_gateway_error` 가 처리 (0.1.1).
- `ValueError` 는 `async with tool_errors():` 안에서 raise 해야 `ToolError` 가 된다.
