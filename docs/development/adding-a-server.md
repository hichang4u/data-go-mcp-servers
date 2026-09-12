# 새 서버 추가하기 / 기존 서버에 API 추가하기

목표 소요: API 하나당 2시간 안팎 (문서 분석 30분, 클라이언트·툴 40분, 테스트 30분, 문서 20분).

## 새 서버인가, 기존 서버의 툴인가

먼저 정한다. 사용자 설정은 서버 단위라 서버가 늘수록 설정이 번거롭다.

- **기존 서버에 툴 추가** — 그 서버의 툴을 돕거나 같은 주제 축인 API (코드 변환, 번호 매핑, 같은 대상의 다른 면). 예: 법정동코드·고용보험 → nps, 기업기본정보·주식시세 → fsc.
- **새 서버** — 주제가 다르고 혼자서도 쓰이는 API (날씨, 대기오염, 관광).

기존 서버에 넣을 때는 1(골격 생성)을 건너뛰고 `api_client.py` 에 `BaseDataGoClient` 서브클래스를 **하나 더** 만든다 (`key_env_prefix` 는 그 서버 것을 그대로). 테스트는 `tests/test_<api>_api.py` 로 나누고, fixture 는 같은 `conftest.py` 에. 나머지 절차는 같고, 6(등록)에서 "새 서버 등록" 대신 "기존 서버에 API 추가 시" 를 따른다.

## 0. API 분석

data.go.kr 의 해당 API 페이지에서 확인할 것:

- 엔드포인트 URL 과 오퍼레이션 목록 (예: `…/B552015/NpsBplcInfoInqireServiceV2/getBassInfoSearchV2`)
- 응답 형식 파라미터 이름 (`dataType`, `type`, `resultType`, `returnType` 중 무엇인지) 와 XML 전용 여부
- 응답 래핑: 표준 `response/header/body` 인지, odcloud 형식인지
- 요청 파라미터의 camelCase 이름, 필수 여부, 형식·범위 제한 (조회 기간 한도 등)
- 활용신청을 하고 `scripts/check_apis.py` 식으로 실제 응답을 한 번 받아 둔다 — **테스트 fixture 로 쓴다**
- 엔드포인트는 활용신청 승인 페이지의 **End Point 를 그대로** 쓴다. 추측한 경로는 코드 30(미등록)이나 12(폐기)로 헷갈리게 실패한다 (주식시세: `/1160100/GetStockSecuritiesInfoService_V2/…`, `service/` 없음)
- 문서에 있는 파라미터가 **실제로 동작하는지** 실호출로 확인한다. 무시되는 파라미터가 있다 (주식시세 `crno`, 고용산재 `v_saeopjangNm`). 필터가 없는 파라미터를 툴에 노출하면 전체 데이터가 돌아온다
- 같은 대상이 여러 행으로 오는지 본다 (기업기본정보는 유효기간별 스냅샷, 주식시세는 일자별). 툴이 무엇을 한 건으로 볼지 정한다

## 1. 골격 생성

```bash
uv run cookiecutter template/ -o src/
# api_name: weather-forecast          (kebab-case, 디렉터리/패키지명)
# api_display_name / api_korean_name / api_base_url ...
```

생성물: `src/weather-forecast/` — `pyproject.toml`(core 의존 포함), `data_go_mcp/weather_forecast/{api_client,models,server}.py`, `tests/`. 훅이 루트에서 `uv sync --dev --all-packages` 와 템플릿 테스트를 돌린다 (uv 가 PATH 에 없으면 직접 실행).

명명 규칙: 디렉터리·패키지 `weather-forecast`, 모듈 `weather_forecast`, 환경변수 접두어 `WEATHER_FORECAST`, 콘솔 스크립트 `data-go-mcp.weather-forecast`.

## 2. 테스트 먼저

`tests/conftest.py` 에 0 단계에서 받은 실응답을 fixture 로 넣는다. 그 다음 `tests/test_api.py` 와 `tests/test_server.py` 를 쓰고 **실패하는 것을 확인**한 뒤 구현한다. 패턴은 [testing.md](testing.md).

## 3. 클라이언트

`api_client.py` — `BaseDataGoClient` 서브클래스에 클래스 속성과 엔드포인트별 메서드만:

```python
class WeatherForecastAPIClient(BaseDataGoClient):
    base_url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"
    key_env_prefix = "WEATHER_FORECAST"
    default_params = {"dataType": "JSON"}

    async def get_forecast(self, nx: int, ny: int, base_date: str, base_time: str = "0500",
                           page_no: int = 1, num_of_rows: int = 100) -> dict[str, Any]:
        body = await self.get("getVilageFcst", {
            "nx": nx, "ny": ny, "base_date": base_date, "base_time": base_time,
            "pageNo": page_no, "numOfRows": num_of_rows,
        })
        return {
            "items": [ForecastItem(**i).model_dump() for i in normalize_items(body)],
            "total_count": body.get("totalCount", 0),
        }
```

- 응답이 XML 이면 `response_format = "xml"`, `pyproject.toml` 의존성을 `data-go-mcp-core[xml]` 로.
- 래핑이 다르면 `_check_response` 오버라이드 (예: `src/nts-business-verification`).
- 검증 실패는 `ValueError` 로 던진다. dict 로 오류를 돌려주지 않는다.

## 4. 모델

`models.py` — 응답 필드를 `Field(default=None, alias="camelName", description="…")` 로. `model_config = ConfigDict(populate_by_name=True)`. 필수 필드는 최소화한다 (XML 은 빈 요소가 `None` 으로 온다).

## 5. 툴

`server.py` — [architecture.md](architecture.md) 의 툴 정의 규약대로. 체크리스트:

- [ ] `@mcp.tool(annotations=READ_ONLY)`
- [ ] 모든 파라미터에 `Annotated[..., Field(description=...)]`
- [ ] 본문 전체를 `async with tool_errors():` 안에
- [ ] 반환은 JSON 직렬화 가능한 dict (또는 포맷된 str)
- [ ] `main()` 은 템플릿 그대로 (`configure_logging`, 키 경고, `mcp.run()`)
- [ ] API 의 범위 제한(기간, 최대 건수)을 docstring 에 적는다

## 6. 등록

### 기존 서버에 API 추가 시

- `tests/test_list_tools.py::SERVERS` 의 그 서버 툴 집합에 추가
- `tests/test_integration.py::CALLS` 에 새 툴 실호출 1건
- `scripts/check_apis.py::TARGETS` 에 `"<server> (<API 별칭>)"` 이름으로 엔드포인트 추가
- `docs/guide/servers/<server>.md`: 첫 문단, 데이터셋 표(신청 페이지 링크, 오퍼레이션명), 활용신청 행("N개 API 모두"), 예시 프롬프트, 알아둘 것 → `uv run python scripts/gen_tool_docs.py`
- `docs/guide/api-keys.md` 신청 표의 그 서버 행에 API 추가, `docs/guide/troubleshooting.md` 의 "결과가 비어 있을 때"
- `README.md` 서버 표(툴 목록), `CLAUDE.md`·README 의 API 개수
- `src/<server>/CHANGELOG.md` 에 Added, `pyproject.toml` 버전 bump (minor)
- `docs/development/PLAN.md` 의 해당 항목에 드러난 사실 기록

### 새 서버 등록 시

- `tests/test_list_tools.py` 의 `SERVERS` 에 모듈과 툴 이름 추가
- `tests/test_integration.py` 의 `CALLS` 에 실호출 1건 추가
- `scripts/check_apis.py` 의 `TARGETS` 에 엔드포인트 추가
- `scripts/gen_tool_docs.py` 의 `SERVERS` 에 추가 → `docs/guide/servers/<server>.md` 작성 후 `uv run python scripts/gen_tool_docs.py`
- 루트 `README.md` 서버 표, `docs/guide/installation.md` 표, `docs/guide/api-keys.md` 신청 표에 한 줄씩
- `src/<server>/README.md`, `CHANGELOG.md`

## 7. 확인

```bash
uv run pytest                                  # 전체
uv run pytest -m integration                   # 실호출 (.env 에 API_KEY)
uv run ruff check src scripts tests && uv run ruff format --check src scripts tests
uv run pyright src scripts tests
uv run python -m data_go_mcp.weather_forecast.server   # 기동 확인 (Ctrl+C)
```

Claude 세션에서 만들 때는 `.claude/commands/add-mcp-server.md` 슬래시 커맨드가 위 절차를 안내한다.
