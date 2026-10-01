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

## S3 — 테스트·품질 `[x]` 2026-09-12 — D3, D11, NFR-3/6

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

- 완료 기준: pytest 전부 통과, ruff 0, pyright 0, CI 4개 매트릭스 + lint 모두 필수 green → **충족**
- 3.1–3.4 는 S2 에서 서버별 테스트를 respx/인프로세스 Client 로 전부 재작성하면서 이미 끝남.
- 3.5: `tests/test_integration.py` (서버당 실호출 1건, `integration` 마커) + 루트 `conftest.py` 가 `.env` 를 읽어 키 없으면 skip.
  로컬 `uv run pytest -m integration` 6 passed / 키 없이 6 skipped 확인.
- 3.6/3.7: 잔여 ruff 7건, pyright 27건(전부 원본 모델의 `Field(None, …)`) 수정. fsc `json_encoders` 는 `field_serializer` 로 교체 → 경고 0.
- 3.8: CI lint 필수화(src/scripts/tests), `.pre-commit-config.yaml` (uv run ruff/pyright).
- 코드리뷰(`/code-review main..s3-quality high`) 1건: 모델 전체 `@field_serializer("*") -> Any` 가 직렬화 스키마의 타입을 전부 `Any` 로 지움
  → 금액 필드에만 `Annotated[Decimal, PlainSerializer(float, return_type=float)]` 별칭 적용, 스키마 타입 보존 테스트 추가.
- 결과: **207 passed, 0 warnings, ruff 0, pyright 0**. 브랜치 `s3-quality`.

## S4 — 문서·배포 `[x]` 2026-09-12 — D10, FR-7/8

| # | 태스크 | 대상 |
|---|---|---|
| 4.1 | `docs/creating-new-mcp-server.md`, `CONTRIBUTING.md`, `TEMPLATE_USAGE.md`, `.claude/*` 를 MCPServer/ToolError/respx/FR-3 기준으로 갱신. macOS/Windows 경로 병기 | docs |
| 4.2 | `docs/step-by-step-example.md` 상단에 "원저장소 시점 기록" 주석 | docs |
| 4.3 | core 의존 해석 방식 결정: 서버 `pyproject.toml`에 `[tool.uv.sources] data-go-mcp-core = { git = …, subdirectory = … }` vs PyPI 선배포 → PRD §9-3 갱신 | `src/*/pyproject.toml`, PRD |
| 4.4 | README: `uvx --from git+…#subdirectory=src/<server>` 설정 예시(Claude Desktop, Claude Code), 6개 서버 상태 표, deprecated 표시(FR-7) | `README.md` |
| 4.5 | 서버별 README/CHANGELOG 갱신, 버전 0.3.0 bump, core 0.1.0 | `src/*/` |
| 4.6 | 태그 `v0.3.0`, GitHub Release 노트 | git |
| 4.7 | 새 환경(다른 venv 또는 다른 PC)에서 README만 보고 Claude Desktop 연결 → 툴 호출 1회 성공 | 검증 |

- 완료 기준: PRD §7 성공 지표 3개 충족 → **충족** (아래)
- 4.3 결정: **git 직접 설치**. `uvx --from git+…#subdirectory=src/<server>` 가 저장소 전체를 받아 `workspace = true` 소스를 그대로 해석하므로
  core 를 따로 배포할 필요 없음. `uv tool run` 으로 nts 서버 기동 → `list_tools` → `check_business_status` 실호출 확인. PyPI 는 보류.
- 문서 구조: `README`(사용자) / `CONTRIBUTING` + `CLAUDE.md`(개발) / `docs/guide`(설치·키·문제해결·서버별 레퍼런스) /
  `docs/development`(아키텍처·서버 추가·테스트·릴리스·PRD·PLAN) / `docs/history`(원저장소 기록) / `docs/api-specs`.
  `creating-new-mcp-server.md`, `TEMPLATE_USAGE.md`, `.claude/subagents` 는 흡수 후 삭제.
- 서버별 툴 레퍼런스는 `scripts/gen_tool_docs.py` 가 `list_tools()` 스키마에서 생성하고 CI 가 `--check` 로 어긋남을 잡는다.
- FR-7(deprecated 표시)은 죽은 API 가 없어 적용 대상 없음. 서버 버전 0.3.0, 태그 `v0.3.0`.

## S5 — 추가 공공데이터 연동 `[x]` (5.1–5.4 완료 2026-09-13, 태그 `v0.4.0`; 5.5 이후는 보류)

2026-09-12 검토. 아래 API 는 **활용신청·엔드포인트·응답 구조를 아직 확인하지 않은 후보**다. 착수 전에
`scripts/check_apis.py` 방식으로 생존·권한을 먼저 확인하고, 절차는 [adding-a-server.md](adding-a-server.md)를 따른다.

설계 원칙: 다른 서버를 돕는 작은 조회(코드 변환, 번호 매핑)는 새 서버가 아니라 **기존 서버에 툴을 추가**한다.
서버 수가 늘면 사용자 설정(`mcpServers` 항목)이 늘어나므로, 서버당 툴을 늘리는 쪽을 우선한다.

### 5a. 기존 서버를 완성하는 것 (1순위)

| # | API | 형태 | 이유 | 붙일 곳 |
|---|---|---|---|---|
| 5.1 `[x]` | 행정안전부_행정표준코드_법정동코드 ([15077871](https://www.data.go.kr/data/15077871/openapi.do), `1741000/StanReginCd`) | 비표준 JSON: `{"StanReginCd":[{"head":[…]},{"row":[…]}]}`, 결과 없음은 `{"RESULT":{"resultCode":"INFO-3"}}` | nps 검색이 지역 코드를 요구하는데 사용자는 코드를 모른다 | nps 에 `find_region_code` 툴 (브랜치 `s5-region-code`, nps 0.4.0) |
| 5.2 `[x]` | 금융위원회_기업기본정보 ([15043184](https://www.data.go.kr/data/15043184/openapi.do), `GetCorpBasicInfoService_V2/getCorpOutline_V2`; V1 은 폐기 코드 12) | 표준 JSON. `corpNm` 부분 일치, `bzno`/`crno` 정확 일치 | fsc 는 법인등록번호 13자리만 받는다. 회사명/사업자번호 → 법인번호 매핑이 없어 nts → fsc 체인이 끊긴다 | fsc 에 `find_corp_number` + `get_corp_outline` (브랜치 `s5-corp-number`, fsc 0.4.0) |
| 5.3 `[x]` | 금융위원회_주식시세정보 ([15094808](https://www.data.go.kr/data/15094808/openapi.do), `1160100/GetStockSecuritiesInfoService_V2/getStockPriceInfo_V2` — `service/` 세그먼트 없음, V1 폐기) | 표준 JSON | 재무제표 옆에 시가총액·주가 | fsc 에 `get_stock_price` + `search_stock_items` (브랜치 `s5-stock-price`, fsc 0.5.0) |
| 5.4 `[x]` | 근로복지공단_고용/산재보험 현황정보 ([15059256](https://www.data.go.kr/data/15059256/openapi.do), `B490001/gySjbPstateInfoService/getGySjBoheomBsshItem`) | 표준 XML | nps 가입자 수와 함께 기업 규모. **사업자등록번호**로 조회돼 nts/fsc 와 조인 | nps 에 `get_insurance_status` (브랜치 `s5-insurance`, nps 0.5.0) |

### 5b. 범용성이 큰 것 (2순위)

| # | API | 비고 |
|---|---|---|
| 5.5 | 기상청_단기예보 (`VilageFcstInfoService_2.0`) | 가장 많이 쓰이는 공공 API. 위경도 → 격자(nx, ny) 변환을 서버 안에서 해줘야 쓸 만하다 |
| 5.6 | 한국환경공단_에어코리아 대기오염정보 | 측정소별 미세먼지. 시도명으로 조회 |
| 5.7 | 국토교통부_아파트 실거래가 | 법정동코드 + 년월. 5.1 과 묶으면 좋다. XML 응답이었던 기억 — 확인 필요 |
| 5.8 | 식품의약품안전처_의약품 허가정보 / e약은요 | msds 와 같은 "물질 안전" 축. XML |
| 5.9 | 한국관광공사_TourAPI | 지역·키워드 관광지. 응답 구조가 표준이라 템플릿 그대로 |

### 5c. 정책·정치 축 (3순위, presidential 과 짝)

| # | API | 제약 |
|---|---|---|
| 5.10 | 열린국회정보 의안정보 | data.go.kr 밖. 키 체계가 다르고 `_check_response` 오버라이드 필요 |
| 5.11 | 법제처 국가법령정보 | 별도 키(law.go.kr). 위와 같은 제약 |

### 5.1 에서 드러난 것

- nps `search_business` 의 지역 코드는 원본 설명(시군구 5자리, 읍면동 8자리)과 달리 **시도 2 / 시군구 3 / 읍면동 3자리**
  (`StanReginCd` 의 `sido_cd`/`sgg_cd`/`umd_cd` 그대로). 실호출로 확인 — 옛 설명대로 넣으면 0건. 하위 코드는 상위 코드와 함께
  줘야 적용된다(시군구만 주면 무시).
- 법정동코드 API 는 별도 활용신청이 필요하다(코드 30). `check_apis.py` 에 7번째 대상으로 추가.
- 툴 결과에 `level`(시도/시군구/읍면동/리)과 `nps_params` 를 붙여 LLM 이 코드 조립 없이 바로 체인할 수 있게 함. 리는 nps 필터가
  없으므로 소속 읍면동 코드를 준다.
- `ValueError` 는 `async with tool_errors():` 안에서 raise 해야 `ToolError` 로 변환된다 (밖에서 raise 하면 `UnexpectedToolError`).

### 5.2 에서 드러난 것

- 응답이 **유효기간(`fstOpegDt`~`lastOpegDt`)별 스냅샷**이라 같은 crno 가 여러 번 온다(삼성전자 19건). `totalCount` 도 스냅샷 수.
  클라이언트 `latest_per_crno` 로 법인별 최신만 남기고, 툴 메시지에 "N corporation(s) in M record(s)" 로 둘을 구분.
- 공시 대상이 아닌 법인은 대부분 필드가 빈 문자열 → `CorpOutline.from_api` 가 None 으로 정규화.
- `corpNm` 은 LIKE 검색이라 "카카오" 는 182 레코드. 페이지(100) 안에서만 dedupe 되므로 이름을 구체적으로 주라고 문서에 적음.

### 5.3 에서 드러난 것

- 엔드포인트가 다른 금융위 API 와 달리 `/1160100/service/…` 가 아니라 `/1160100/GetStockSecuritiesInfoService_V2/…`. 활용신청 페이지의
  End Point 를 그대로 믿어야 한다 (추측한 경로는 코드 30/12).
- `crno` 파라미터는 문서에 있지만 **무시된다**(전체 4,446,353건 반환). 법인 → 종목 연결은 `get_corp_outline.enp_pban_cmpy_nm`
  (공시회사명) 을 `itmsNm` 에 넣는 방식으로 문서화.
- 결과 없음이 `items.item: []` — 재무정보 API 의 `items: ""` 와 다르지만 core `normalize_items` 가 둘 다 처리.
- 종목 목록(`likeItmsNm`)은 전 일자에 걸친 행이라, 1건 조회로 최신 거래일을 알아낸 뒤 그 날짜로 다시 조회해 종목당 한 건으로 만든다 (2회 호출).
- 나머지 오퍼레이션 3개는 실호출로 확인 후 제외: 수익증권시세는 ETF 가 아니라 상장 펀드 수익증권 87종(`KODEX` 0건), 신주인수권증권 4종, 신주인수권증서 0건. 이들 단축코드는 `0036221D` 처럼 8자리 영숫자라 주식용 6자리 숫자 검증과 다르다 — 나중에 추가하면 `srtn_cd` 검증을 분리할 것. ETF 는 별도 API 에서.

### 5.4 에서 드러난 것

- 고용24(옛 워크넷) 채용정보 API 도 검토했으나 포털 밖(별도 `authKey`), XML, 코드표 의존, 회사명으로만 조인 → 보류. 근로복지공단 API 가
  같은 키·자동승인·사업자번호 조인이라 목적에 더 맞았다.
- 13개 오퍼레이션 중 사업장 상세(`getGySjBoheomBsshItem`)만 채택. 사업종류 검색은 `eopjongNm1` 파라미터로 동작 확인했지만 쓰임이 좁고,
  요율표는 필터 파라미터를 찾지 못해(8,623행 전체 반환) 제외. 나머지는 통계표.
- 사업장 상세는 `v_saeopjaDrno`(10자리 전체) 외 필터가 없다(`v_saeopjangNm` 무시). `opaBoheomFg` 생략 시 산재+고용 모두.
- 업종 요소가 보험 종류에 따라 `sjEopjong*`/`gyEopjong*` 로 갈리고 값에 뒤 공백이 붙는다 → 모델에서 통합·strip.
- 빈 결과는 `<items/>` → xmltodict `None` → core `normalize_items` 가 처리. nps 패키지에 `data-go-mcp-core[xml]` 의존 추가.
- 코드리뷰: core `_gateway_error` 가 JSON 만 봐서 XML 서비스의 게이트웨이 오류(403 + XML `OpenAPI_ServiceResponse`)가 `HTTP 403: <?xml…` 로,
  200 으로 오면 빈 결과로 새어 나갔다 → core 0.1.1 에서 XML 도 파싱. msds 도 같은 혜택.

### 착수 순서 제안

1. 5.1 법정동코드 — 반나절. nps 사용성 즉시 개선
2. 5.2 기업기본정보 — 법인번호 매핑으로 nts → fsc 체인 완성
3. 5.5 단기예보 — 사용자층 확대

각 항목은 브랜치 `s5-<slug>` 에서 TDD 로 진행하고, 툴 추가 시 `gen_tool_docs.py` 와 `docs/guide/api-keys.md` 의 활용신청 표를 갱신한다.

## S6 — OpenDART 전자공시 `[x]` 2026-09-17, 태그 `v0.5.0` — 새 서버 `dart-disclosure`

첫 **data.go.kr 밖** 서버. 검토 배경: fsc 의 재무 툴은 연간·요약 위주고 공시 목록·원문, 분기 재무제표, 사업보고서 세부는 DART 만 준다.
비교 대상이던 hjsh200219/korea-public-data-mcp(TS, 호스팅형, 운영자 키)의 DART action 구성(6개)과 기업코드 스냅샷 동봉 방식을 참고했다 (라이선스 없음 → 코드는 새로 씀).

### 드러난 것

- OpenDART 키는 data.go.kr 키와 무관한데 `load_api_key` 가 `API_KEY` 로 fallback 하면 조용히 `[010]` 이 난다 → core 0.2.0 에 `BaseDataGoClient.shared_key=False` / `key_url`, `DataGoAPIError(source=)`(오류 접두어 `OpenDART 오류`). 루트 conftest 의 integration skip 은 `API_KEY` 기준이라 `test_integration.py` 에 `KEY_ENV` 로 서버별 키 skip 을 추가.
- 응답은 `{"status","message",...}` 평면. `013` 은 "조회된 데이타가 없습니다" — 없는 `corp_code` 도 013. `list.json` 의 항목에는 문서와 달리 `pblntf_ty` 가 없고 `report_nm` 에 꼬리 공백이 붙는다.
- `list.json` 은 `bgn_de` 생략 시 **당일만** 검색한다 (회사 지정해도) → 클라이언트가 기본 시작일을 채운다 (회사 있으면 1년, 없으면 30일; 회사 없이 3개월 초과는 `[100]`).
- `corpCode.xml` 은 ZIP(30MB XML, 119,352개사, 상장 3,990). 이름 검색 API 가 없어 필수 → 파싱 결과를 `corp_codes.json.gz`(1.5MB) 로 동봉. 영문명은 상장사만 넣어 1.2MB 절약. `corp_name` 은 `삼성전자`, `company.json` 은 `삼성전자(주)` 로 표기가 다르다.
- `document.xml` ZIP 에는 본문 `<rcept_no>.xml` 과 첨부 `<rcept_no>_NNNNN.xml` 이 함께 있고 파일 순서는 본문이 마지막일 수 있다 → 이름으로 고른다. 본문은 HTML 인데 meta 는 euc-kr, 실제 바이트는 UTF-8. 사업보고서 본문 6.3MB → 텍스트 66만 자 → `offset`/`max_chars` 페이징.
- ZIP 엔드포인트의 오류(잘못된 접수번호, 키)는 HTTP 200 + XML `<result><status>` → `_get_zip` 이 `PK` 매직으로 분기.
- 주요계정(`fnlttSinglAcnt`) 금액은 쉼표 포함 문자열, 전체 재무제표(`fnlttSinglAcntAll`)는 쉼표 없음 → 모델 validator 가 둘 다 int 로. 사업보고서 전체 계정은 213행 → `sj_div` 클라이언트 필터.

## S7 — Smithery 등록 `[x]` 2026-09-20, 태그 `v0.6.0` — 통합 서버 `all-servers` + MCPB 번들

시작은 서버별 `smithery.yaml` 9개(구형 `startCommand: stdio` + `commandFunction`)였는데, 2026-09-19 Smithery 문서(`build/publish`, `concepts/cli`, `build/session-config`)에는 `smithery.yaml` 이 전혀 없다 — 등록 경로는 **URL(Streamable HTTP)** 과 **MCPB 번들(stdio)** 둘뿐이고 CLI 도 `npx @smithery/cli install` 이 아니라 `smithery mcp add`. yaml 은 전부 버렸다.

리스팅 하나 = 프로세스 하나라 서버 7개를 한 프로세스로 합친 `src/all-servers` 를 만들었다 (리스팅 1개, 키 입력 2칸). 서버별 7개 리스팅은 필요해지면 manifest 만 더 만들면 된다.

### 드러난 것

- 등록된 `Tool` 을 꺼내는 공개 API 는 없다 → 읽기만 `_tool_manager._tools` (mcp 마이너 업그레이드 때 깨질 수 있어 테스트로 잡는다). 넣는 쪽은 `MCPServer(tools=[...])` 공개 인자. 툴 이름은 7개 서버 합쳐 36개, 충돌 없음.
- 자동 탐색은 `server` 모듈이 없거나 `mcp` 가 `MCPServer` 가 아닌 네임스페이스 패키지를 건너뛴다 — 원저장소 PyPI 배포판(같은 `data_go_mcp` 네임스페이스)과 한 환경에 있어도 import 시점에 죽지 않게.
- 서버 목록은 `pkgutil.iter_modules(data_go_mcp.__path__)` 로 자동 탐색 — 네임스페이스 패키지라 editable 워크스페이스와 site-packages 설치 양쪽에서 동작 확인. 단 uvx 는 선언된 의존성만 설치하므로 `all-servers/pyproject.toml` 의존성이 진짜 목록이고, 테스트가 `src/*` 와 대조한다.
- MCPB 0.4 에 `server.type: "uv"` 가 있다: 번들에 `pyproject.toml` 만 넣으면 호스트가 uv 로 의존성을 설치한다. 네이티브 휠(pydantic-core) 때문에 OS 별 번들이 필요했을 `python` 타입을 피할 수 있다. 번들 `pyproject.toml` 의 `[tool.uv.sources]` 가 git 태그를 가리키고, all-servers → 개별 서버 → core 의 워크스페이스 의존성은 uv 가 git 체크아웃 안에서 해석한다 (로컬 path 소스로 `uv run --directory … src/server.py` → 툴 36개 확인).
- 각 서버 `server.py` 의 `load_dotenv()` 는 호출 프레임의 파일 위치에서 위로 `.env` 를 찾는다 — editable 설치에서는 저장소 `.env` 를 읽어 테스트가 헷갈렸다. 배포 번들(site-packages)에서는 무관.
- Smithery 가 `type: uv` 번들을 받아 주는지, 등록 후 `smithery mcp add … --client claude` 가 `user_config` 두 칸을 제대로 묻는지는 **실제 publish 로 확인해야 한다** (미검증). 태그 `v0.6.0` 을 push 한 뒤 pack → Claude Desktop 설치 확인 → publish.

### Smithery 등록 뒤 Claude Desktop 실사용에서 드러난 것 (2026-09-20)

- pps 낙찰(`search_successful_bids`)이 "성공, 0건": 나라장터 오류 응답은 `{"response": …}` 가 아니라 `{"nkoneps.com.response.ResponseError": {"header": {…}}}` 라 core `_check_response` 가 통과시켰다 → pps 클라이언트가 오버라이드. 그리고 낙찰 API 의 개찰일시 범위는 문서의 1주가 아니라 **하루**(24h+1분까지 OK, 이틀은 07)라 기본 7일 조회가 늘 07 이었다. 기본을 오늘(주말이면 직전 금요일)로, 여러 날은 `ValueError`. 날짜 필터 자체는 동작 (물품 하루 약 2만 건, 용역 6천 건, 공사 9만 건).
- 같은 날 Claude Desktop 4개 툴 집중 테스트에서 추가로: 계약(`search_contracts`)의 한도도 문서(1개월)와 달리 **7일**(8일부터 07). `get_bid_detail` 은 999건×3페이지 훑기라 하루 1,100건 이상인 요즘엔 2~3일 범위를 넘으면 못 찾았다 → 기본 7일·12페이지로. 999건 한 페이지가 2.3초, 응답이 날짜순이 아니라 범위를 좁히는 것만이 해법. 공고번호(`R26BK01699006`)는 날짜와 대략 단조 증가하지만 역산은 안 했다. 근본 해법은 별도 API(나라장터 입찰공고정보서비스 `getBidPblancListInfoServcPPSSrch`, `bidNtceNo` 검색 지원)를 활용신청해 붙이는 것 — 보류.

## S8 — 다음 후보 조사 `[ ]` 2026-09-29 — 실호출로 생존·키 확인만 한 단계

착수 전 조사. 2026-09-29 에 전부 실제로 호출해 본 결과이며, 응답 구조·파라미터 동작은 아직 안 봤다.

### A. 우리 키로 이미 열려 있는 것 (활용신청 불필요 — `00 정상` 확인)

| API | 엔드포인트 | 메모 |
|---|---|---|
| 조달청 나라장터 **입찰공고정보서비스** | `/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch` (물품 `…ThngPPSSrch`, 공사 `…CnstwkPPSSrch`) | 지금 pps 가 쓰는 개방표준서비스보다 필드가 훨씬 많다. 경로 접두어가 `ao` 가 아니라 **`ad`** |
| 조달청 나라장터 **낙찰정보서비스** | `/1230000/as/ScsbidInfoService/getOpengResultListInfoServcPPSSrch` | 접두어 **`as`** |

- 접두어를 못 찾으면 `NO_OPENAPI_SERVICE_ERROR` 가 난다. `BidPublicInfoService01`~`07` 같은 버전 접미어는 전부 없음 — 접두어(`ad`/`as`/`ao`)가 갈림.
- **미해결**: `bidNtceNo` 가 `inqryDiv=2` 에서도 무시된다(753건 전체 반환, `bidNtceOrd` 를 같이 줘도 같음). `get_bid_detail` 의 단건 조회를 이걸로 대체하려면 다른 오퍼레이션을 더 봐야 한다. `inqryDiv=2` + 기간은 `07`.

### B. 엔드포인트 살아 있음, 활용신청만 하면 되는 것 (`SERVICE_KEY_IS_NOT_REGISTERED`)

기상청 단기예보(`1360000/VilageFcstInfoService_2.0`), 에어코리아(`B552584/ArpltnInforInqireSvc`),
국토부 아파트 매매 실거래(`1613000/RTMSDataSvcAptTradeDev`), 식약처 e약은요(`1471000/DrbEasyDrugInfoService`),
관광공사(`B551011/KorService2`), 소상공인 상권정보(`B553077/api/open/sdsc2`),
심평원 병원정보(`B551182/hospInfoServicev2`), 중기부 창업기업DB(`B552735/kisedKstartupService01`).

### C. data.go.kr 밖 포털 (dart 처럼 새 서버 + `shared_key = False`)

| 포털 | 키 | 확인 결과 |
|---|---|---|
| 한국은행 ECOS | 무료 신청, **`sample` 키로 개발 가능** | `StatisticSearch/sample/json/kr/1/5/722Y001/M/…` → 기준금리 3.5 수신 |
| 법제처 국가법령정보 | `OC=<아이디>` | `OC=test` 로 도로교통법 검색 성공 |
| 서울 열린데이터광장 | 무료 즉시, `sample` 키 있음 | `openapi.seoul.go.kr:8088/sample/…` → 799건 수신 |
| 열린국회정보 | 무료 즉시 발급 필요 | 키 없이는 `Bad Request` |
| KOSIS | 무료 신청 필요 | `유효하지 않은 인증KEY입니다` (엔드포인트는 살아 있음) |
| 금감원 FINLIFE | 무료 신청 필요 | https 307 리다이렉트 — 호출 방식 더 확인 필요 |
| KRX 데이터 | — | 403, 공식 OpenAPI 아님 |

### 우선순위 제안

1. **한국은행 ECOS** — 새 서버. 기준금리·환율·물가를 fsc 재무/dart 공시 옆에 둔다. `sample` 키로 TDD 가 가능해 마찰이 가장 적다
2. **국토부 아파트 실거래** — nps 의 `find_region_code`(법정동코드)를 그대로 재사용할 수 있다
3. **기상청 단기예보** — 범용성 1위지만 위경도 → 격자(nx, ny) 변환을 서버가 해줘야 쓸 만하다
4. **조달청 입찰공고정보서비스** — 새 서버가 아니라 pps 보강. 키가 이미 열려 있어 즉시 착수 가능

## S9 — 한국은행 ECOS `[x]` 2026-09-29, 태그 `v0.7.1` — 새 서버 `bok-ecos`

S8 조사에서 1순위로 고른 것. data.go.kr 밖 두 번째 포털이고, 키 마찰이 가장 적다 (`sample` 키로 개발·테스트 가능).

### 드러난 것

- **인증키가 경로 세그먼트**다: `/api/{서비스}/{키}/json/kr/{시작}/{끝}/{조건…}`. `BaseDataGoClient` 는 키를 쿼리에 넣으므로 `request()` 에서 경로를 직접 조립한다 (`_check_response` 는 그대로 재사용).
- 오류는 `{"RESULT": {"CODE","MESSAGE"}}`. `INFO-200` 은 "해당하는 데이터가 없습니다" → dart 의 `013` 처럼 빈 결과로 바꾼다. `INFO-100` 은 키 오류.
- `sample` 키는 **한 번에 10건**까지 (`ERROR-301`, 메시지에 "sample은 최대 10건 이내에서 호출이 가능합니다"). 실키는 100건씩 받는다 → `page_size` 를 키에 따라 바꾼다.
- **통계표 이름 검색 API 가 없다.** `StatisticTableList` 는 전체(844건) 또는 코드 단건만 준다 → 전체를 받아 이름으로 거르고 프로세스 안에 캐시. `SRCH_YN=N` 은 분류 노드라 제외.
- 시점 형식이 주기를 따른다: 분기는 `2023Q1` (`20231` 은 `ERROR-101`). `StatisticItemList` 의 `START_TIME`/`END_TIME` 이 그 형식 그대로 오므로 툴 체인이 자연스럽다. 같은 항목이 주기마다 한 줄씩 온다.
- `StatisticSearch` 의 항목 코드는 **생략 가능**하고, 생략하면 통계표의 모든 항목이 온다 (722Y001 3개월 = 27건). 최대 4개.
- "100대 통계지표" 는 실제로 **101건** — 기본 조회 100건이면 한 건이 잘린다 (실키로만 드러남). 기본값 200.
- `KeyStatisticList` 의 `CYCLE` 은 주기 코드가 아니라 **기준 시점**(`20260929`)이다 → 모델에서 `time` 으로 받는다.

## S10 — 국토교통부 실거래가 `[x]` 2026-09-30, 태그 `v0.8.0` — 새 서버 `molit-realestate`

S8 조사의 2순위. 공통 `API_KEY` 라 설정 칸이 늘지 않고, nps 의 `find_region_code`(법정동코드)가 그대로 입력이 된다.

### 드러난 것

- **API 11개가 종류별로 따로**다 (매매 7: 아파트·오피스텔·연립다세대·단독다가구·상업업무용·공장창고(`RTMSDataSvcInduTrade`)·토지 / 전월세 4: 앞의 넷). 공장창고는 상업업무용과 필드 구성이 같다. 각각 활용신청이 필요하다. 툴을 10개로 늘리는 대신 `property_type` 파라미터로 묶어 **툴 2개**로 했다 (분양권 전매는 미신청, 범위 밖).
- **잘못된 입력이 오류가 아니라 0건으로 온다**: 10자리 코드, 4자리 년월, `LAWD_CD` 누락 모두 `resultCode 000 / totalCount 0`. 사용자는 "그 달에 거래가 없다"로 오해한다 → 클라이언트가 형식을 먼저 검증. `find_region_code` 가 주는 10자리는 앞 5자리로 잘라 받아들이되, **시도 코드(`1100000000` → `11000`)는 거부한다** — 잘라도 LAWD_CD 가 아니라 역시 0건이 온다 (코드리뷰에서 잡힘).
- **정상 코드가 `00` 이 아니라 `000`** 이다 → core `_check_response` 가 오류로 판정해서 오버라이드했다.
- 필드 이름·개수가 종류마다 다르다 (아파트 32개 ~ 단독다가구전월세 15개). 공통은 `dealYear/Month/Day`, `sggCd`, `umdNm` 뿐. 이름 필드도 `aptNm`/`offiNm`/`mhouseNm` 로 갈리고 단독다가구·상업업무용·토지는 아예 없다.
- **면적은 뜻이 달라 한 필드로 합치면 안 된다**: 전용(`excluUseAr`), 연면적(`totalFloorAr`), 대지(`plottageAr`), 대지권(`landAr`), 건물(`buildingAr`), 토지 거래면적(`dealArea`).
- 금액은 `"790,000"` 쉼표 문자열의 **만원** 단위. 해제된 거래가 섞여 오므로(`cdealType`) `cancelled` 로 표시한다. 지번은 `1***` 처럼 마스킹되기도 한다.
- 아파트 전월세는 도로명 필드가 소문자(`roadnm`)다 — 매매(`roadNm`)와 다르다.

## S11 — 지수·ETF `[x]` 2026-09-30, 태그 `v0.8.1` — fsc 서버에 툴 2개

"KRX 도 연동했나" 라는 질문에서 시작. `data.krx.co.kr` 은 403 에 공식 API 가 아니고, 주식시세는 이미 fsc 에 있다. 빠진 것은 **지수와 ETF** 였다.

### 드러난 것

- 금융위 지수시세정보·증권상품시세정보 **V2 가 주식시세와 같은 경로 규칙**이다 (`/1160100/GetMarketIndexInfoService_V2/getStockMarketIndex_V2`, `service/` 없음). `service/…` V1 도 살아 있지만 주식시세 V1 이 폐기됐던 전례가 있어 V2 를 쓴다.
- 한 서비스에 오퍼레이션이 둘씩이다 (주가지수/채권지수, ETF/ETN) → molit 처럼 종류 파라미터로 묶어 **툴 2개**로.
- **`idxCsf`(지수 계열) 필터는 무시된다** — `basDt` 만 줄 때와 결과 수가 같다(171). 툴 파라미터에 넣지 않았다. `idxNm`/`likeIdxNm`/`basDt`/기간은 동작.
- 채권지수는 필드가 완전히 다르다 (총수익지수·듀레이션·ytm) → 별도 모델.
- ETF 는 `nav`, ETN 은 `indcVal`; 상장수도 `stLstgCnt`/`lstgScrtCnt` 로 갈린다 → 한 모델에서 이름을 통일하되 값의 뜻이 다르므로 필드는 나눠 둔다.
- ETF/ETN 단축코드는 `0219E0` 처럼 **영숫자 6자리** — 주식시세의 숫자 6자리 검증을 쓰면 안 된다 (S5 때 예고됐던 것).

## S12 — 낙찰업체 조회 `[x]` 2026-09-30, 태그 `v0.9.0` — pps 에 툴 1개

"기관을 가로지르는 조회" 포지셔닝 점검에서 나온 것. 사업자번호 하나로 국세청→금융위(법인번호→재무)→근로복지(고용)까지는 이어지는데 **나라장터 낙찰 이력만 끊겨 있었다**.

### 드러난 것

- 개방표준서비스의 낙찰정보에는 **업체 정보가 없다**. 낙찰업체 사업자번호·상호·대표자는 낙찰정보서비스(`as/ScsbidInfoService/getScsbidListSttus*`) 응답에만 있다.
- 그런데 `bidwinnrBizno`/`bidwinnrNm` 을 요청으로 주면 **무시된다** (3,199건 그대로) → 기간을 훑어 거르는 수밖에 없다.
- `PPSSrch` 가 붙은 오퍼레이션은 **부분집합**이다 (같은 날 같은 축에서 53건 vs 357건) → 전수 쪽을 쓴다.
- `inqryDiv=1` 은 등록일시, **`2` 가 개찰일시**다. 축을 잘못 잡으면 개찰일이 기간 밖인 건이 섞인다.
- `numOfRows=1000` 을 주면 **10건만 온다** (999가 상한, 조용한 오작동).
- **한 요청의 기간 한도는 1개월**(초과 시 코드 07). 3개월 측정은 달 단위로 나눠 부른 것이었는데 첫 구현이 이를 빠뜨려 2개월 이상이 즉시 실패했다 (코드리뷰 후 발견) → `_monthly_windows` 로 분할. 실측: 용역 1개월 6,095건 = 7페이지 21초, 3개월 16,867건 = 59초.
- 페이지 상한에 걸려 덜 훑으면 "0건"이 없다는 뜻으로 읽힌다 → `complete` 플래그를 두고 메시지에 경고를 붙인다. 3개월 × 3종은 61요청 221초라 툴 한 번으로는 무리 → 업무구분 하나, 최대 3개월로 제한.
- 오래된 달일수록 건수가 많다 (7월 7,498 > 9월 3,272). 정정·추가 등록이 쌓이기 때문으로 보인다 (추정).

## S13 — 고용24 채용정보 `[x]` 2026-10-01 — 새 서버 `work24-jobs`

S5.4 에서 "포털 밖, 회사명으로만 조인"이라며 보류했던 것. 다시 보니 **사업자등록번호로 필터된다** — 보류 사유가 틀렸다.

### 드러난 것

- 옛 워크넷 엔드포인트(`openapi.work.go.kr/opi/...`)는 전부 404. 2024-09 고용24 통합으로 `www.work24.go.kr/cm/openApi/call/wk/...` 로 옮겼다.
- data.go.kr 의 "워크넷 채용정보"는 등록유형이 **LINK** — 포털이 중계하지 않아 공통 `API_KEY` 로는 안 된다. 키는 고용24에서 **서비스별로** 신청 (채용정보만 열려 있고 채용행사·공채속보·임금체불은 미신청 상태였다).
- 응답 `wanted` 에 **`busino`(사업자등록번호 10자리, 마스킹 없음)** 가 있고 **요청 필터로도 동작**한다. 나라장터 낙찰과 정반대 — 기간 훑기가 필요 없다.
- 지역코드가 **법정동코드 앞 5자리와 호환**(`11680` 강남구 550건). molit 과 달리 **시도 코드도 동작**한다 (`11000` 서울 5,996건).
- **조용히 무시되는 파라미터**: `busiNo`(대소문자), `regionCd`, `empTpCd` → 전국 5만여 건이 그대로 온다. 틀린 이름을 보내면 "회사 공고"를 "전국 공고"로 착각한다.
- `display` 상한 100 (1000 을 줘도 100). `returnType=JSON` 은 빈 응답 — XML 만 쓴다.
- 오류 래핑이 둘이다: 미신청은 `<GO24><error>`, 그 외는 `<wantedRoot><messageCd>` (006 = 결과 없음, 018 = 상세의 `infoSvc` 누락).
- 결과가 **하나면 `<wanted>` 가 dict, 여럿이면 list** 로 온다. core `normalize_items` 는 `items.item` 모양 전용이라 단건을 빈 목록으로 만들었다 — 회사 하나 조회가 이 서버의 핵심 용례인데 조용히 0건이 됐다 (코드리뷰에서 잡힘).
- `006`(결과 없음)은 목록에선 빈 결과지만 **상세에선 그 공고가 없다는 뜻**이다. 한데 묶으면 '공고는 있는데 내용이 비었다'로 읽힌다.
- 상세(`210D01`)는 **`infoSvc` 가 필수**다 (문서에서 못 찾았고 실호출로 알아냈다). 상세에 종업원 수·자본금·연 매출액이 있어, 금융위 재무정보에 없는 비상장사의 규모를 알 수 있다.

## 일정 요약

| 스프린트 | 예상 | 선행 조건 |
|---|---|---|
| S0b | 완료 | — |
| S1 | 0.5d | — |
| S2 | 완료 | — |
| S3 | 완료 | — |
| S4 | 완료 | — |
| S5 | 완료 (5.1–5.4; 5.5 이후 보류) | 항목별 활용신청 |

S0~S4 전부 2026-09-12 하루에 완료 (계획 3.5d).
