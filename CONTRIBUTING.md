# Contributing

## 시작

```bash
git clone https://github.com/hichang4u/data-go-mcp-servers && cd data-go-mcp-servers
uv sync --dev --all-packages
uv run pre-commit install
cp .env.example .env                           # 실호출 테스트용 키 (주석 참고), 커밋되지 않는다
uv run pytest
```

Python 3.10+, [uv](https://docs.astral.sh/uv/). 설계는 [docs/development/architecture.md](docs/development/architecture.md), 테스트 관례는 [docs/development/testing.md](docs/development/testing.md).

## 무엇을 기여할 수 있나

- **새 공공 API** — [docs/development/adding-a-server.md](docs/development/adding-a-server.md) 의 절차대로. 기존 서버의 주제와 맞으면 그 서버에 툴을 추가하고(클라이언트 클래스 하나 더), 아니면 템플릿(`uv run cookiecutter template/ -o src/`)으로 새 서버를 만든다.
- **기존 서버의 툴 개선** — 툴 이름·파라미터는 하위호환을 지킨다. 바꿔야 하면 새 선택 파라미터를 추가한다.
- **API 변경 대응** — `uv run python scripts/check_apis.py` 로 확인하고, 실응답을 `tests/conftest.py` fixture 에 반영한다.

## 규칙

### 코드

- 모든 함수에 타입 힌트, Google 스타일 docstring (한/영 병기 권장), 모든 API 호출은 비동기.
- 툴: `@mcp.tool(annotations=READ_ONLY)`, 파라미터마다 `Field(description=)`, 본문은 `async with tool_errors():`. 오류를 dict 로 돌려주지 않는다.
- 클라이언트: `BaseDataGoClient` 상속. 검증 실패는 `ValueError`.
- pydantic: `Field(default=None, …)` (위치 인자 금지), `ConfigDict(populate_by_name=True)`.
- `data_go_mcp/__init__.py` 를 만들지 않는다 (네임스페이스 패키지).
- 서버별 `pyproject.toml` 에 pytest/ruff 설정을 두지 않는다. 설정은 루트 하나.
- 로그는 stderr 로만 (`configure_logging`). stdout 은 MCP 프로토콜 채널이다.

### 테스트

- 테스트를 먼저 쓰고 실패를 본 뒤 구현한다.
- HTTP 는 `respx`, 툴 호출은 인프로세스 `mcp.Client(mcp)`. fixture 는 실응답.
- 서버당 `test_api.py`(클라이언트, API 가 여럿이면 `test_<api>_api.py`) + `test_server.py`(툴, `isError` 경로 포함), 그리고 루트 `tests/test_list_tools.py`·`test_integration.py`·`scripts/check_apis.py` 에 한 줄씩 등록.

### 품질 게이트

PR 은 CI(ubuntu/windows × 3.10/3.13)에서 다음이 모두 통과해야 한다:

```bash
uv run pytest
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
uv run pyright src scripts tests
```

### 커밋

Conventional Commits: `feat(nps): …`, `fix(core): …`, `docs: …`, `test: …`, `refactor(pps): …`, `chore(release): …`. scope 는 서버 디렉터리의 앞 단어 또는 `core`, `template`, `scripts`.

브랜치는 `main` 에서 따고, 스프린트/기능 단위로 PR. 리뷰에서 나온 수정은 테스트를 먼저 추가하고 고친다.

### 환경변수

키는 `API_KEY`(공통) 또는 `<SERVER>_API_KEY`(서버별, 우선). 문서·예시·템플릿 모두 이 규칙을 따른다. data.go.kr 이 아닌 포털(OpenDART)의 서버는 `shared_key = False` 로 공통 키를 끄고 `<SERVER>_API_KEY` 만 받는다 — 그 키를 `.env.example` 에 주석과 함께 추가한다. 키를 코드나 fixture 에 넣지 않는다.

### 문서

- 툴 시그니처를 바꾸면 `uv run python scripts/gen_tool_docs.py` 로 `docs/guide/servers/*.md` 를 갱신한다.
- 사용자 대상 문서(`README.md`, `docs/guide/`)에는 내부 용어(스프린트 번호, D#/FR# 등)를 쓰지 않는다.
- 서버 패키지의 `README.md` 는 짧게 유지하고 가이드 페이지로 링크한다. `CHANGELOG.md` 에 변경을 적는다.

## 도움

이슈: https://github.com/hichang4u/data-go-mcp-servers/issues
