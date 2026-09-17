# PRD — data-go-mcp-servers (mcp 2.x 재정비)

- 상태: Draft v0.2 (2026-09-12) — core 패키지 추출 결정 반영
- 저장소: https://github.com/hichang4u/data-go-mcp-servers
- 기반: [Koomook/data-go-mcp-servers](https://github.com/Koomook/data-go-mcp-servers) (Apache-2.0, 2025-09-17 이후 정지)

## 1. 배경

한국 공공데이터 API 6종을 MCP 서버로 감싼 원저장소는 구조와 문서가 잘 갖춰져 있으나
`mcp` SDK 2.x 출시 이후 설치 자체가 불가능해졌고 유지보수가 중단됐다. 이 프로젝트는
원저장소의 설계(서버당 독립 패키지, 템플릿 기반 확장, 한/영 docstring)를 유지하면서
**현재 SDK에서 동작하고, 테스트가 통과하며, Windows에서도 개발·배포가 되는 상태**로
재정비한다.

### 1.1 원저장소 문서 분석 요약

`docs/`, `CONTRIBUTING.md`, `TEMPLATE_USAGE.md`, `.claude/`를 읽고 정리한 것.

| 문서 | 내용 | 이 PRD에 반영한 점 |
|---|---|---|
| `docs/creating-new-mcp-server.md` | 새 서버 추가 10단계 가이드 + 체크리스트 | 서버 추가 절차(§5.4)의 골격으로 채택. 단 `FastMCP` import, `mcp.list_tools()` 동기 호출, dict 기반 에러 반환, macOS 전용 경로 등 현 SDK/OS와 맞지 않는 예시는 갱신 대상 |
| `docs/step-by-step-example.md` | NTS 서버를 약 2시간에 만든 실제 기록 (템플릿 5분 → 클라이언트 20분 → 모델 15분 → 툴 30분 → 테스트 20분 → 로컬 10분 → 문서 15분 → 배포 10분) | "서버 1개 추가 ≤ 2시간"을 확장성 목표(§7)로 채택 |
| `docs/MSDS_API_명세서.md` | 안전보건공단 MSDS OpenAPI 1.1 (2024-06) 명세. `chemlist` + `chemdetail01~16` 17개 오퍼레이션, **XML 전용**, 엔드포인트 `msds.kosha.or.kr` | msds 서버는 data.go.kr 게이트웨이를 거치지 않으므로 키 발급처가 다를 수 있음 → 미결 사항(§9) |
| `CONTRIBUTING.md` | 코드 스타일(ruff, Google docstring, 전 함수 타입 힌트, 전 API 비동기), Conventional Commits, 서버별 README/CHANGELOG 필수 | 비기능 요구사항(§4.2)으로 승계 |
| `TEMPLATE_USAGE.md`, `template/` | cookiecutter 템플릿 + `scripts/create_mcp_server.py` | 유지. 단 `post_gen_project.py`가 생성된 하위 디렉터리에서 `git init`을 실행해 **모노레포 안에 중첩 저장소를 만드는 버그** 있음 → 수정 대상 |
| `.claude/commands`, `.claude/subagents` | API 문서를 붙여넣으면 서버를 생성하는 Claude 워크플로 | 유지. 환경변수명을 `{API_NAME}_API_KEY`로 안내하는데 실제 코드는 전부 `API_KEY` → 규칙 통일 필요(§4.1 FR-3) |

문서 간 불일치로 확인된 것:

- 환경변수명: 코드·README 28곳 `API_KEY` vs docs 7곳 `NTS_BUSINESS_VERIFICATION_API_KEY`
- 에러 처리: 문서·코드 모두 `{"error": ...}` dict 반환 → MCP `isError` 미전달
- 문서의 `mcp.list_tools()`는 실제로는 코루틴이라 예시 테스트가 그대로는 동작하지 않음

## 2. 목표 / 비목표

### 목표
1. 6개 서버 전부 `mcp>=2.2,<3`에서 기동하고 `list_tools`/`call_tool`이 동작한다.
2. `uv run pytest`가 루트에서 한 번에 돌고 전부 통과한다. 서버당 최소 1개 mocked 테스트.
3. Windows/Linux 양쪽에서 개발·테스트·배포 스크립트가 동작한다.
4. 새 data.go.kr API를 서버로 추가하는 데 2시간 이내(문서·템플릿·Claude 워크플로 갱신).
5. 원저장소의 알려진 결함(§3)을 모두 해소한다.

### 비목표
- 원저장소 PyPI 네임스페이스(`data-go-mcp.*`)로의 배포 — 소유권이 없다.
- 새로운 공공 API 서버 추가 — 기존 6종 정비가 끝난 뒤 별도 PRD. → 정비 완료 후 [PLAN.md](PLAN.md) S5 로 진행 (2026-09-13, v0.4.0: 기존 서버에 API 4종 추가, 새 서버는 만들지 않음). S6 (2026-09-17, v0.5.0) 에서 첫 새 서버 `dart-disclosure` — data.go.kr 밖(OpenDART) 이라 core 에 공통 키 fallback 을 끄는 옵션이 생겼다.
- HTTP/SSE 전송 지원 — stdio만 대상. (MCPServer가 지원하므로 나중에 켤 수는 있음)
- 원저장소로의 upstream PR — 응답 가능성이 낮아 우선순위 없음. 단 fork 관계와 라이선스 표시는 유지.

## 3. 현재 확인된 결함 (Phase 0 기준선)

| # | 결함 | 영향 | 확인 방법 |
|---|---|---|---|
| D1 | `mcp[cli]>=1.13.0` 상한 없음 | mcp 2.x 설치 시 `ModuleNotFoundError: mcp.server.fastmcp` — 6개 서버 전부 기동 불가 | 로컬 재현 |
| D2 | `fsc-financial-info/data_go_mcp/__init__.py` 존재 | `data_go_mcp` 네임스페이스 패키지 파괴 — 같은 환경에 서버 2개 이상 설치 시 import 실패 | 로컬 재현, Phase 0에서 제거함 |
| D3 | 테스트 3건 실패 (nps 1, fsc 2), 3개 서버 테스트 부재 | CI 불가 | pytest 59 passed / 3 failed |
| D4 | 툴 에러를 `{"error": ...}` dict로 반환 | LLM이 실패를 정상 결과로 오인 | 코드 리뷰 |
| D5 | nts/pps/msds/presidential `main()`의 `print()` | stdio 프로토콜 채널 오염 가능 | 코드 리뷰 |
| D6 | nps `httpx.AsyncClient(verify=False)` | 불필요한 TLS 검증 비활성화 | 코드 리뷰 |
| D7 | `deploy_to_pypi.py`의 `rm -rf`/`mv` subprocess | Windows에서 배포 불가 | 코드 리뷰 |
| D8 | 의존성 명세 불일치 (fsc만 `mcp>=1.0.0`, `httpx>=0.24.0`) | 서버별 해석 차이 | pyproject 비교 |
| D9 | 템플릿 post-gen 훅의 `git init` | 모노레포 안 중첩 저장소 생성 | 코드 리뷰 |
| D10 | 문서/템플릿이 `FastMCP`·`{API_NAME}_API_KEY` 등 코드와 불일치 | 신규 서버 추가 시 혼란 | 문서 분석 |
| D11 | ruff 917건, pyright 46건 | 품질 게이트 부재 | Phase 0 측정 |

## 4. 요구사항

### 4.1 기능 요구사항

| ID | 요구사항 | 우선순위 |
|---|---|---|
| FR-1 | 6개 서버가 `mcp.server.mcpserver.MCPServer`로 기동하고 기존 툴 이름·파라미터를 그대로 노출한다 (하위호환) | P0 |
| FR-2 | 툴 실패는 `ToolError`로 raise 해 클라이언트에 `isError=True`로 전달한다. 원인별로 (a) 입력 검증 실패 (b) API resultCode≠00 (c) HTTP/네트워크 오류를 메시지로 구분한다 | P0 |
| FR-3 | API 키는 `API_KEY`(공통)를 기본으로 읽되, 서버별 `<SERVER>_API_KEY`(예: `NPS_BUSINESS_ENROLLMENT_API_KEY`)가 있으면 우선한다. 문서·템플릿·Claude 워크플로를 이 규칙으로 통일한다 | P0 |
| FR-4 | 모든 조회 툴에 `ToolAnnotations(readOnlyHint=True, openWorldHint=True)`를 단다 | P1 |
| FR-5 | `scripts/check_apis.py`로 6개 엔드포인트 생존을 한 번에 확인할 수 있다 | P1 |
| FR-6 | 서버 로그는 stderr로만 나간다. stdout에는 MCP 메시지 외 아무것도 쓰지 않는다 | P0 |
| FR-7 | 죽은 것으로 확인된 API의 서버는 README에 "deprecated"로 표시하고 CI 대상에서 제외한다 (삭제하지 않음) | P1 |
| FR-8 | Claude Desktop / Claude Code 에서 git 직접 설치(`uvx --from git+...`)로 쓸 수 있는 설정 예시를 README에 둔다 | P1 |

### 4.2 비기능 요구사항

| ID | 요구사항 |
|---|---|
| NFR-1 | Python 3.10–3.13, `uv` workspace. 서버당 독립 패키지(hatchling), `data_go_mcp` 네임스페이스 패키지 (`data_go_mcp/__init__.py` 금지) |
| NFR-2 | 의존성 통일: `mcp[cli]>=2.2,<3`, `httpx>=0.28`, `pydantic>=2.11`, `python-dotenv>=1.1`, XML 서버만 `xmltodict>=0.14` |
| NFR-3 | CI: ubuntu/windows × 3.10/3.13 에서 pytest 필수 통과. ruff/pyright는 Phase 3 완료 시점부터 필수 |
| NFR-4 | 코드 스타일은 CONTRIBUTING.md 승계 — ruff(format+check), Google docstring, 전 함수 타입 힌트, 전 API 비동기 |
| NFR-5 | 커밋: Conventional Commits (`feat(nps): ...`, `fix(fsc): ...`) |
| NFR-6 | 테스트: HTTP는 `respx`로 mocking. 실호출 테스트는 `@pytest.mark.integration` + `API_KEY` 존재 시에만 실행 |
| NFR-7 | 배포 스크립트는 `shutil`/`pathlib`만 사용 (셸 명령 의존 금지) |
| NFR-8 | 서버별 README.md, CHANGELOG.md 유지. 툴 docstring은 한/영 병기 |

## 5. 설계

### 5.1 mcp 1.x → 2.x 대응표 (mcp 2.2.0에서 확인)

| 항목 | 1.x | 2.x |
|---|---|---|
| import | `from mcp.server.fastmcp import FastMCP` | `from mcp.server.mcpserver import MCPServer` |
| 생성 | `FastMCP("name")` | `MCPServer("name", instructions=..., version=...)` |
| 툴 등록 | `@mcp.tool()` | 동일. `annotations=`, `structured_output=` 추가 가능 |
| 실행 | `mcp.run()` | 동일 (`transport="stdio"` 기본) |
| 에러 | — | `from mcp.server.mcpserver.exceptions import ToolError` |
| 저수준 API | `@server.list_tools()` / `@server.call_tool()` 데코레이터 | 제거됨. `Server(name, on_list_tools=..., on_call_tool=...)` 생성자 방식. 이 프로젝트는 저수준 API를 쓰지 않는다 (fsc를 S1에서 `MCPServer`로 이전) |
| 클라이언트 타입 | `CallToolResult.isError` | `CallToolResult.is_error` (snake_case) |

### 5.2 공통 클라이언트 패키지 `data-go-mcp-core` (결정: 추출)

6개 `api_client.py`에 중복된 것: snake→camel 변환, `response.header.resultCode` 검사,
`body.items.item` 단일/배열 정규화, 에러코드 표(fsc에만 있음), XML→dict 파싱, API 키
로딩(FR-3), `httpx.AsyncClient` 수명 관리.

`src/data-go-mcp-core/` 를 workspace 멤버로 추가하고 6개 서버가 `data-go-mcp-core`에 의존한다.

```
src/data-go-mcp-core/
├── pyproject.toml                # name = "data-go-mcp-core"
└── data_go_mcp/core/
    ├── __init__.py
    ├── client.py                 # BaseDataGoClient
    ├── errors.py                 # DataGoAPIError, RESULT_CODES
    ├── keys.py                   # load_api_key(server_prefix)  ← FR-3
    └── xml.py                    # parse_xml_response (xmltodict 의존은 extras "xml")
```

`BaseDataGoClient` 계약:

```python
class BaseDataGoClient:
    base_url: ClassVar[str]
    key_env_prefix: ClassVar[str]        # 예: "NPS_BUSINESS_ENROLLMENT"
    response_format: ClassVar[Literal["json", "xml"]] = "json"

    def __init__(self, api_key: str | None = None, *, timeout: float = 30.0): ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, *exc) -> None: ...
    async def get(self, endpoint: str, params: Mapping[str, Any]) -> dict[str, Any]: ...
    async def post(self, endpoint: str, json: Any, params: Mapping[str, Any] | None = None) -> dict[str, Any]: ...
    # get/post 는 serviceKey 주입 → 요청 → HTTP 오류 → resultCode 검사 → body 반환까지 처리
    # None 값 파라미터 제거, items.item 단일/배열 정규화 포함

def to_camel(snake: str) -> str: ...
def normalize_items(body: Mapping[str, Any]) -> list[dict[str, Any]]: ...
```

odcloud(nts, presidential)는 `response/header` 래핑이 없고 `status_code`/`currentCount`
구조라 `BaseDataGoClient`의 `_check_response` 훅을 오버라이드해서 대응한다.
KOSHA(msds)는 XML 전용이므로 `response_format = "xml"`.

각 서버의 `api_client.py`는 엔드포인트별 메서드와 Pydantic 파싱만 남긴다.
git 직접 설치(`uvx --from git+...#subdirectory=src/<server>`) 시 core가 workspace 소스로
해석되지 않으므로, 각 서버 `pyproject.toml`의 `[tool.uv.sources]`에
`data-go-mcp-core = { git = "...", subdirectory = "src/data-go-mcp-core" }` 를 두거나
PyPI에 core를 먼저 올려야 한다. **Phase 4에서 확정** (§9-3과 함께).

### 5.3 에러 처리 규약

```python
# api_client.py
class DataGoAPIError(Exception):
    def __init__(self, result_code: str, result_msg: str): ...

# server.py
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True))
async def search_business(...) -> dict[str, Any]:
    try:
        async with NPSAPIClient() as client:
            return await client.search_business(...)
    except DataGoAPIError as e:
        raise ToolError(f"data.go.kr 오류 {e.result_code}: {e.result_msg}") from e
    except httpx.HTTPError as e:
        raise ToolError(f"HTTP 오류: {e}") from e
```

### 5.4 새 서버 추가 절차 (문서 갱신 방향)

`docs/creating-new-mcp-server.md`의 10단계 구조는 유지하되:
1. 코드 예시를 `MCPServer`/`ToolError`/`respx` 기준으로 교체
2. Claude Desktop 설정 예시를 macOS/Windows 양쪽으로
3. 환경변수 규칙을 FR-3으로 통일
4. `template/hooks/post_gen_project.py`에서 `git init` 제거
5. `docs/step-by-step-example.md`는 역사 기록으로 두고 상단에 "원저장소 시점 기록" 주석

## 6. 마일스톤

| Phase | 산출물 | 완료 기준 | 상태 |
|---|---|---|---|
| 0. 기준선 | 원본 vendoring, `mcp<2` 임시 핀, CI, `check_apis.py` | CI에서 로컬과 동일한 3건 실패 재현 | **완료** (2026-09-12) |
| 0b. API 생존 확인 | `check_apis.py` 실행 결과를 README에 기록 | 6개 각각 살아있음/죽음 판정 | **완료** (2026-09-12, 6개 전부 정상) |
| 1. mcp 2.x | D1, D8 해소. 임시 핀 제거 | 6개 서버 `list_tools` 동작, 기존 테스트 결과 유지 | **완료** (2026-09-12) |
| 2. 결함 수정 | `data-go-mcp-core` 추출(§5.2) 후 6개 서버 이전, D4–D7, D9 해소, FR-2/3/4/6 | core 단위 테스트 + 서버별 기존 테스트 유지 | **완료** (2026-09-12, 195 passed; D3도 해소) |
| 3. 테스트·품질 | D3, D11 해소, NFR-3/6 | pytest 전부 통과, ruff 0, pyright 0, CI 전부 필수 | **완료** (2026-09-12, 207 passed) |
| 4. 문서·배포 | D10 해소, FR-7/8, 버전 bump(0.3.0), CHANGELOG | 새 환경에서 README만 보고 Claude Desktop 연결 성공 | **완료** (2026-09-12, v0.3.0) |
| 5. 확장 (PRD 범위 밖, PLAN S5) | 법정동코드·고용산재보험 → nps, 기업기본정보·주식시세 → fsc | 툴별 실호출 통과, API 당 코드리뷰 | **완료** (2026-09-13, v0.4.0, 263 passed) |
| 6. 새 서버 (PLAN S6) | OpenDART → `dart-disclosure`, core 0.2.0 | 실호출 6툴 통과, 코드리뷰 6건 처리 | **완료** (2026-09-17, v0.5.0, 334 passed) |

## 7. 성공 지표

- `uvx --from git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/<server> data-go-mcp.<server>` 가 7개 모두 기동
- CI 4개 매트릭스 전부 green, ruff/pyright 필수화
- 서버 1개 추가 소요 ≤ 2시간 (템플릿 → 테스트 → README)

## 8. 리스크

| 리스크 | 대응 |
|---|---|
| ~~1년 방치 동안 API 엔드포인트·스키마 변경~~ | 해소 — 0b에서 6개 엔드포인트 모두 정상 응답 확인. 스키마 변경은 S2 이전 시 실응답 fixture로 검증 |
| mcp 2.x 마이너 릴리스에서 API 변동 | `<3` 상한 + CI 매트릭스로 조기 감지 |
| ~~MSDS 키 발급처가 data.go.kr가 아닐 가능성~~ | 해소 — data.go.kr 키로 호출 확인 |
| ~~원저장소 PyPI 패키지와 이름 충돌~~ | 해소 — PyPI 를 쓰지 않는다 (git 직접 설치) |

## 9. 미결 사항

1. ~~MSDS(KOSHA) API 키가 data.go.kr 키와 동일한지~~ — 동일 키로 `resultCode 00` 확인 (2026-09-12, 해결)
2. ~~공통 클라이언트 패키지 추출 여부~~ — 추출하기로 결정 (§5.2). 배포 방식은 3번과 함께 결정
3. ~~PyPI 재배포 네임스페이스 및 core 의존 해석 방식~~ — git 직접 설치로 결정 (2026-09-12). uv 가 git 체크아웃의 workspace 소스를 해석하므로 core 별도 배포 불필요. PyPI 는 필요해질 때 재검토
4. ~~`requires-python` 하한~~ — mcp 2.2.0의 `Requires-Python: >=3.10` 확인. 3.10 유지 (해결)
