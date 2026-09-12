# 실행 계획 (스프린트)

- 근거: [PRD.md](PRD.md) §3 결함(D#), §4 요구사항(FR/NFR), §6 마일스톤
- 원칙: Phase 하나 = 스프린트 하나. 스프린트는 순서대로 진행하되, S0b(API 생존 확인)만 키가
  준비되는 즉시 끼워 넣는다. 각 스프린트 끝에 CI green(알려진 실패 제외)과 README/PRD 갱신.
- 커밋 단위: 태스크 하나당 커밋 하나. Conventional Commits (`feat(core): …`, `fix(nps): …`).
- 상태 기호: `[ ]` 미착수 `[~]` 진행 중 `[x]` 완료

## S0 — 기준선 `[x]` 2026-09-12

- [x] 원본 vendoring, `mcp<2` 임시 핀, CI, `scripts/check_apis.py`
- [x] D2 제거, pytest importlib 모드
- 결과: pytest 59 passed / 3 failed, ruff 917, pyright 46

## S0b — API 생존 확인 `[x]` 2026-09-12

- [x] `.env`에 `API_KEY` 설정 후 `uv run python scripts/check_apis.py` (2026-09-12)
- [x] 6개 결과를 README "현재 상태" 표에 기록 — nts/pps/msds 정상, nps/fsc/presidential 은 코드 30/401 (활용신청 미완)
- [x] MSDS(KOSHA)가 같은 키로 응답 → PRD §9-1 해결
- [x] nps(3046071) / fsc(15043459) / presidential(15084167) 활용신청 후 재실행 → 6개 전부 정상
- [x] 죽은 API 없음 → FR-7 적용 대상 없음
- 완료 기준: 6개 서버 각각 살아있음/죽음 판정이 README에 있음

## S1 — mcp 2.x 전환 `[x]` 2026-09-12 — D1, D8, FR-1

| # | 태스크 | 대상 파일 |
|---|---|---|
| 1.1 | 루트 `constraint-dependencies = ["mcp<2"]` 제거 | `pyproject.toml` |
| 1.2 | 6개 서버 + 템플릿 의존성을 NFR-2로 통일 (`mcp[cli]>=2.2,<3`, `httpx>=0.28`, `pydantic>=2.11`, `python-dotenv>=1.1`, XML 서버만 `xmltodict>=0.14`) | `src/*/pyproject.toml`, `template/…/pyproject.toml` |
| 1.3 | `from mcp.server.fastmcp import FastMCP` → `from mcp.server.mcpserver import MCPServer`, `FastMCP(` → `MCPServer(` | `src/*/…/server.py`, 템플릿 `server.py` |
| 1.4 | `uv lock && uv sync --dev --all-packages` | `uv.lock` |
| 1.5 | fsc `test_list_tools`의 `patch('mcp.server.Server.list_tools')` 를 `await mcp.list_tools()` 직접 호출로 교체 | `src/fsc-financial-info/tests/test_server.py` |
| 1.6 | 루트 `tests/test_list_tools.py` 추가: 6개 서버 모듈을 import 해 `await mcp.list_tools()` 가 비어 있지 않은지 확인. `testpaths`에 `tests` 추가 | `tests/`, `pyproject.toml` |
| 1.7 | README 기준선 표 갱신 (mcp 2.2 기준 수치) | `README.md` |

- 완료 기준: mcp 2.2에서 6개 서버 `list_tools` 통과, 실패 테스트가 S0의 3건 그대로(늘지 않음) → **충족** (65 passed / 3 failed)
- 실제 작업 중 추가된 것:
  - fsc는 `FastMCP`가 아니라 저수준 `mcp.server.Server`의 `@server.list_tools()` 데코레이터를 쓰고 있었고, 2.x에서 이 API가
    생성자 `on_list_tools=` 방식으로 바뀌어 import는 되지만 기동 시 `AttributeError`. → `MCPServer` 4개 툴로 재작성
    (툴 이름·파라미터·출력 문구 동일, 실 API 호출로 확인). 1.5는 이 재작성에 흡수.
  - 1.6의 스모크 테스트는 모듈 import가 아니라 실제 stdio 서브프로세스 + `ClientSession` 으로 구현 — 구현 방식과 무관하게 검증됨.
  - mcp 2.x 클라이언트 타입은 snake_case (`CallToolResult.is_error`, `Tool.input_schema`). S2/S3 테스트 작성 시 주의.
- 코드리뷰(`/code-review high`, 2026-09-12) 결과 2건:
  - fsc 파라미터 설명 유실 — `MCPServer`는 docstring `Args:`를 파싱하지 않아 옛 `inputSchema`의 per-parameter description이
    사라졌음. `Annotated[..., Field(description=...)]`로 복구 (수정 완료). **나머지 5개 서버도 같은 상태(원본부터)** → S2 2.15에서
    annotations 달 때 함께 `Field(description=)` 적용.
  - `tests/test_list_tools.py`가 `API_KEY`를 주입해 no-key 경로의 stdout `print()`(D5)를 못 잡음 → S2 2.16에서 no-key 변형 추가.

## S2 — core 추출 + 결함 수정 `[x]` 2026-09-12 — D4–D7, D9, FR-2/3/4/6

### 2a. `data-go-mcp-core` (0.5d)

| # | 태스크 | 대상 |
|---|---|---|
| 2.1 | 패키지 골격: `src/data-go-mcp-core/pyproject.toml`(`name = "data-go-mcp-core"`, extras `xml = ["xmltodict>=0.14"]`), `data_go_mcp/core/__init__.py` | 신규 |
| 2.2 | `errors.py`: `DataGoAPIError(result_code, result_msg)`, fsc의 `ERROR_CODES` 표를 `RESULT_CODES`로 이전 | 신규 |
| 2.3 | `keys.py`: `load_api_key(prefix)` — `<PREFIX>_API_KEY` 우선, 없으면 `API_KEY`, 둘 다 없으면 `ValueError` (FR-3) | 신규 |
| 2.4 | `client.py`: `BaseDataGoClient` (PRD §5.2 계약). `to_camel`, `normalize_items`, `_check_response` 훅 | 신규 |
| 2.5 | `xml.py`: fsc/pps/msds의 xmltodict 파싱을 `parse_xml_response`로 통합 | 신규 |
| 2.6 | core 단위 테스트 (`respx` 사용): 키 로딩 우선순위, None 파라미터 제거, resultCode≠00 → `DataGoAPIError`, items 단일/배열 정규화, XML 파싱 | `src/data-go-mcp-core/tests/` |
| 2.7 | 루트 dev 그룹에 `respx` 추가 | `pyproject.toml` |

### 2b. 서버 이전 (0.5d) — 쉬운 것부터

| # | 서버 | 특이사항 |
|---|---|---|
| 2.8 | nps | 가장 단순한 JSON. `verify=False` 제거(D6) 동시 처리 |
| 2.9 | pps | JSON + xmltodict 혼용 → `response_format` 확인 |
| 2.10 | fsc | XML/JSON 양쪽 파싱, `ERROR_CODES` → core로 |
| 2.11 | nts | odcloud: `status_code`/`data` 구조 → `_check_response` 오버라이드, POST |
| 2.12 | presidential | odcloud: `currentCount`/`data` 구조 |
| 2.13 | msds | KOSHA XML 전용, `chemdetail01~16` |

각 서버 이전 시: `api_client.py`는 엔드포인트 메서드 + Pydantic 파싱만 남김, 서버 `pyproject.toml`에
`data-go-mcp-core` 의존 추가, 기존 테스트 통과 유지.

### 2c. 서버 공통 결함 (0.5d)

| # | 태스크 | 대상 |
|---|---|---|
| 2.14 | 툴의 `except Exception: return {"error": …}` → `raise ToolError(...)` (PRD §5.3 규약, FR-2) | 6개 `server.py` |
| 2.15 | 모든 툴에 `annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True)` (FR-4) + 파라미터 `Annotated[..., Field(description=)]` (docstring `Args:`는 스키마에 반영되지 않음) | 6개 `server.py` |
| 2.16 | `main()`의 `print()` → `logging`(stderr). 공통 `configure_logging()`을 core에 두고 호출 (D5, FR-6). `tests/test_list_tools.py`에 `API_KEY` 없는 환경에서도 기동·`list_tools` 되는 변형 추가 | 6개 `server.py`, `core/logging.py`, `tests/` |
| 2.17 | `deploy_to_pypi.py`의 `rm -rf`/`mv` → `shutil` (D7, NFR-7) | `scripts/deploy_to_pypi.py` |
| 2.18 | 템플릿 훅에서 `git init` 제거 (D9); 템플릿 `api_client.py`/`server.py`를 core 기반으로 교체 | `template/` |

- 완료 기준: core 테스트 통과, 6개 서버가 core 위에서 동작, S0 실패 3건 외 새 실패 없음, 툴 실패가 Inspector에서 `isError`로 보임
  → **충족**. 결과 195 passed / 0 failed (S0의 실패 3건은 테스트 재작성으로 해소, D3 조기 달성). 브랜치 `s2-core`.
- 진행 방식: superpowers TDD — 모듈/서버마다 테스트 먼저(RED 확인) → 구현(GREEN). 2b와 2c는 서버당 한 번에 처리.
  HTTP는 respx, 툴 호출은 인프로세스 `mcp.Client(mcp)`, fixture는 S0b 실응답.
- 실제 작업 중 드러난 것:
  - **pps `get_bid_detail`** 은 API 범위 제한(1개월)과 맞지 않는 90일/100건 스캔이라 동작 불가였음 → 30일 창 × 999건 × 3페이지 + `start_date/end_date`.
  - **presidential `search_speeches`** 는 현재 페이지 10건만 클라이언트 필터 → odcloud `cond[컬럼::EQ|LIKE]` 서버측 필터로 교체.
    **`get_recent_speeches`** 는 오래된 순 목록의 1페이지(1948년)를 반환하던 버그 → 건수 확인 후 마지막 페이지.
  - odcloud 401 `{"code":-401,"msg":…}` 형태를 core `_gateway_error` 가 `DataGoAPIError` 로 매핑 (테스트 먼저).
  - 서버별 `pyproject.toml` 의 `[tool.pytest.ini_options]`/`[tool.ruff]` 가 루트 설정을 가리고 있었음 → 전부 제거.
  - `tests/__init__.py` 가 세 곳에 있어 importlib 모드에서 `tests.test_server` 이름이 충돌(fsc 테스트가 nps 경로로 중복 수집) → 제거, 공용 fixture는 `conftest.py`.
  - Windows: `deploy_to_pypi.py` 와 템플릿 훅의 이모지 `print()` 가 cp949 콘솔에서 `UnicodeEncodeError` → `sys.stdout.reconfigure(utf-8)`.
  - 원본 pydantic 모델의 `Field(None, …)` 위치 인자를 pyright 가 필수로 봄 → 손댄 서버는 `Field(default=None, …)` 로 (나머지는 S3 3.7).
  - ruff isort `no-sections = true` (원본 설정) 가 상대 import 를 맨 위로 올리는 등 순서를 망침 → 표준 섹션 + `known-first-party`.
- 코드리뷰(`/code-review main..s2-core high`) 결과 4건, 전부 테스트 먼저 추가 후 수정:
  - presidential `get_recent_speeches`: 마지막 페이지가 `total % limit` 건만 있을 때 limit 미만 반환 → 앞 페이지에서 채움. `limit=0` → ZeroDivisionError → 입력 검증.
  - 서버별 `pyproject.toml` 에서 pytest 섹션 제거 시 `testpaths = ["tests"]` 의 `[` 때문에 `["tests"]` 테이블 잔재 남음 → 제거.
  - `configure_logging` 이 root INFO 를 켜면서 httpx 의 `HTTP Request: GET <url?serviceKey=…>` 가 stderr 에 남음 (키 유출) → httpx/httpcore WARNING.
  - msds: xmltodict 가 빈 요소를 `None` 으로 주어 필수 필드 `ValidationError` 로 툴 전체 실패 가능 → None 제거 + 모델 기본값.

## S3 — 테스트·품질 `[ ]` (1d) — D3, D11, NFR-3/6

| # | 태스크 | 대상 |
|---|---|---|
| 3.1 | nps `test_search_with_mock_response`: `raise_for_status`를 동기 `Mock`, 단언을 dict 접근으로 → respx로 재작성 | nps tests |
| 3.2 | fsc `test_client_initialization_from_env`(env 격리), `test_server_initialization`(버전 하드코딩 제거) | fsc tests |
| 3.3 | 기존 `AsyncMock` 기반 HTTP 모킹을 전부 `respx`로 통일 (NFR-6) | nps/nts/fsc tests |
| 3.4 | pps, presidential, msds에 툴별 최소 1개 mocked 테스트 | 신규 tests |
| 3.5 | `@pytest.mark.integration` 마커 등록, `API_KEY` 없으면 skip 하는 conftest | 루트 `conftest.py`, `pyproject.toml` |
| 3.6 | `ruff check --fix` + `ruff format` 후 잔여 수동 수정 → 0건 | 전체 |
| 3.7 | pyright 46건 → 0건 (주로 Optional 처리, dict 타입) | 전체 |
| 3.8 | CI에서 ruff/pyright `continue-on-error` 제거, `pre-commit` 설정 추가 | `.github/workflows/ci.yml`, `.pre-commit-config.yaml` |

- 완료 기준: pytest 전부 통과, ruff 0, pyright 0, CI 4개 매트릭스 + lint 모두 필수 green

## S4 — 문서·배포 `[ ]` (0.5d) — D10, FR-7/8

| # | 태스크 | 대상 |
|---|---|---|
| 4.1 | `docs/creating-new-mcp-server.md`, `CONTRIBUTING.md`, `TEMPLATE_USAGE.md`, `.claude/*` 를 MCPServer/ToolError/respx/FR-3 기준으로 갱신. macOS/Windows 경로 병기 | docs |
| 4.2 | `docs/step-by-step-example.md` 상단에 "원저장소 시점 기록" 주석 | docs |
| 4.3 | core 의존 해석 방식 결정: 서버 `pyproject.toml`에 `[tool.uv.sources] data-go-mcp-core = { git = …, subdirectory = … }` vs PyPI 선배포 → PRD §9-3 갱신 | `src/*/pyproject.toml`, PRD |
| 4.4 | README: `uvx --from git+…#subdirectory=src/<server>` 설정 예시(Claude Desktop, Claude Code), 6개 서버 상태 표, deprecated 표시(FR-7) | `README.md` |
| 4.5 | 서버별 README/CHANGELOG 갱신, 버전 0.3.0 bump, core 0.1.0 | `src/*/` |
| 4.6 | 태그 `v0.3.0`, GitHub Release 노트 | git |
| 4.7 | 새 환경(다른 venv 또는 다른 PC)에서 README만 보고 Claude Desktop 연결 → 툴 호출 1회 성공 | 검증 |

- 완료 기준: PRD §7 성공 지표 3개 충족

## 일정 요약

| 스프린트 | 예상 | 선행 조건 |
|---|---|---|
| S0b | 완료 | — |
| S1 | 0.5d | — |
| S2 | 완료 | — |
| S3 | 1d | S2 |
| S4 | 0.5d | S3, S0b |

총 3.5d. S0b가 늦어지면 S1–S3는 mocked 응답으로 진행하고 S4 전에 반드시 완료.
