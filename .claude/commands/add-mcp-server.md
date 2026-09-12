---
description: data.go.kr API 하나를 새 MCP 서버로 추가한다 (API 문서를 붙여넣어 시작)
argument-hint: (API 문서 또는 data.go.kr 페이지 URL)
---

새 서버를 추가한다. 절차와 규약은 @docs/development/adding-a-server.md 와 @docs/development/architecture.md 를 따른다. 아래는 그 요약이다.

## 1. 입력 확인

사용자가 준 내용에서 다음을 뽑고, 빠진 것은 물어본다:

- 서비스명(한/영), 엔드포인트 URL 과 오퍼레이션 목록
- 응답 형식 파라미터 이름(`dataType`/`type`/`resultType`/`returnType`)과 XML 전용 여부
- 응답 래핑: 표준 `response/header/body` 인지 odcloud(`status_code`/`data`, `currentCount`/`data`) 인지
- 요청 파라미터(camelCase), 필수 여부, 형식·범위 제한(조회 기간 한도, 최대 건수)
- 활용신청 완료 여부 — 안 됐으면 먼저 하게 한다 (미신청 시 코드 30)
- 사용 예시 프롬프트 2~3개 → 툴 설계의 기준

가능하면 `uv run python -c` 나 `scripts/check_apis.py` 식으로 **실제 응답을 한 번 받아** `tests/conftest.py` fixture 로 쓴다.

## 2. 이름

`api_name` kebab-case 하나에서 나머지가 결정된다: 디렉터리 `src/<api_name>`, 패키지 `data-go-mcp.<api_name>`, 모듈 `data_go_mcp.<api_name_underscore>`, 환경변수 접두어 `<API_NAME_UPPER>` (`<PREFIX>_API_KEY`, 공통 `API_KEY` 도 됨), 콘솔 스크립트 `data-go-mcp.<api_name>`.

## 3. 생성과 구현 (TDD)

```bash
uv run cookiecutter template/ -o src/
```

1. `tests/conftest.py` 에 실응답 fixture
2. `tests/test_api.py`, `tests/test_server.py` 작성 → `uv run pytest src/<api_name>/tests` 로 **실패 확인**
3. `api_client.py`: `BaseDataGoClient` 서브클래스 (`base_url`, `key_env_prefix`, `default_params`, 필요시 `response_format="xml"`, `_check_response` 오버라이드)
4. `models.py`: `Field(default=None, alias="camel", description=…)`, `ConfigDict(populate_by_name=True)`
5. `server.py`: `@mcp.tool(annotations=READ_ONLY)`, 모든 파라미터 `Annotated[…, Field(description=…)]`, 본문 `async with tool_errors():`
6. 통과 확인, `ruff`/`pyright` 클린

## 4. 등록

- `tests/test_list_tools.py::SERVERS`, `tests/test_integration.py::CALLS`, `scripts/check_apis.py::TARGETS`, `scripts/gen_tool_docs.py::SERVERS`
- `docs/guide/servers/<api_name>.md` (다른 서버 페이지를 본떠서, `<!-- tools:start/end -->` 마커 포함) → `uv run python scripts/gen_tool_docs.py`
- `README.md` 서버 표, `docs/guide/installation.md` 표, `docs/guide/api-keys.md` 신청 표
- `src/<api_name>/README.md`, `CHANGELOG.md`

## 5. 완료 기준

- `uv run pytest` 전체 통과 (새 서버 테스트 ≥ 8개: 파라미터 전달, 파싱, 빈 결과, API 오류→`DataGoAPIError`, 툴 annotation/설명, 정상 호출, `isError` 경로, 키 없음)
- `.env` 키로 `uv run pytest -m integration` 의 새 항목 통과
- 커밋 `feat(<scope>): add <api_name> server`
