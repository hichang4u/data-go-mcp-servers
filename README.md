# data-go-kr

한국 공공데이터 포털(data.go.kr) API를 MCP(Model Context Protocol) 서버로 제공하는 프로젝트.
[Koomook/data-go-mcp-servers](https://github.com/Koomook/data-go-mcp-servers)(Apache-2.0)를 기반으로,
`mcp` 2.x SDK 대응과 미해결 결함 수정을 목표로 한다.

## 왜 다시 만드는가

원저장소는 2025-09-17 이후 갱신이 없고, 현재 상태로는 설치 자체가 안 된다.

- `mcp[cli]>=1.13.0`에 상한이 없어 `uvx data-go-mcp.*@latest`가 mcp 2.x를 받아
  `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`로 기동 실패
- 저장소 테스트가 깨져 있고(nps 1건, fsc 2건), 6개 서버 중 3개는 테스트가 없음
- 툴 실패를 예외 대신 `{"error": ...}` dict로 반환해 MCP `isError`가 전달되지 않음
- 일부 서버 `main()`이 stdout에 `print()`해 stdio 전송을 오염
- `deploy_to_pypi.py`가 `rm -rf`/`mv`를 호출해 Windows에서 동작 불가

## 대상 서버

| 서버 | 기관 / API | 상태 |
|---|---|---|
| nps-business-enrollment | 국민연금공단 사업장 가입내역 | core 이전 완료 |
| nts-business-verification | 국세청 사업자등록정보 진위확인·상태조회 | core 이전 완료 |
| pps-narajangteo | 조달청 나라장터 입찰·낙찰·계약 | core 이전 완료 |
| fsc-financial-info | 금융위원회 기업 재무정보 | core 이전 완료 |
| presidential-speeches | 대통령기록관 연설문 | core 이전 완료 |
| msds-chemical-info | 안전보건공단 MSDS 화학물질 정보 | core 이전 완료 |

각 서버는 `src/<server>/` 아래 독립 패키지로 두고 uv workspace로 묶는다.

## 계획

상세 요구사항·설계·결함 목록은 [docs/PRD.md](docs/PRD.md), 스프린트별 태스크는 [docs/PLAN.md](docs/PLAN.md) 참조.

| 단계 | 내용 |
|---|---|
| 0. 기준선 | 원본 clone, `mcp<2` 임시 핀으로 현재 테스트 결과 기록, 6개 API 생존 여부 실호출 확인, CI(pytest/ruff/pyright) 추가 |
| 1. mcp 2.x | `FastMCP` → `mcp.server.mcpserver.MCPServer`, 의존성 `mcp[cli]>=2.2,<3`으로 통일 |
| 2. 결함 수정 | `ToolError` 기반 에러 전달, `print` → `logging(stderr)`, `verify=False` 제거, 배포 스크립트 `shutil` 전환, 공통 클라이언트 추출 |
| 3. 테스트 | 깨진 테스트 수정, `respx`로 HTTP mocking 통일, 서버당 최소 1개 테스트, `integration` 마커로 실호출 분리 |
| 4. 배포 | 버전 bump, git 직접 설치(`uvx --from git+...`) 안내 또는 별도 PyPI 네임스페이스 |

## 현재 상태 (S2 완료, 2026-09-12)

| 항목 | S0 기준선 | S1 (mcp 2.2) | S2 (core 추출) |
|---|---|---|---|
| `uv run pytest` | 59 passed, 3 failed | 65 passed, 3 failed | **195 passed, 0 failed** |
| 6개 서버 stdio 기동 + `list_tools` | — | 통과 | 통과 (API 키 없이도 기동) |
| 툴 실패 → MCP `isError` | 아니오 (`{"error": …}` dict) | 아니오 | **예** (`ToolError`) |
| `ruff check src scripts` | 917건 | 미측정 | 새 코드 0건, 원본 잔여는 S3 |
| `pyright src` | 46 errors | 미측정 | 새 코드 0건, 원본 잔여는 S3 |

S2에서 한 것: 공통 패키지 `src/data-go-mcp-core`(`BaseDataGoClient`, `DataGoAPIError`, `load_api_key`,
`tool_errors`, `READ_ONLY`, `configure_logging`) 를 만들고 6개 서버를 그 위로 이전. 모든 툴에
`readOnlyHint` annotation 과 파라미터 설명, stderr 전용 로깅. 배포 스크립트·템플릿 Windows 대응.
동작하지 않던 툴 수정: pps `get_bid_detail`, presidential `search_speeches`/`get_recent_speeches`.

### API 생존 확인 (`scripts/check_apis.py`, 2026-09-12)

data.go.kr 일반 인증키 1개로 6개 API 모두 정상 응답 확인. nps/fsc/presidential 은 포털에서
활용신청이 필요했고(미신청 시 코드 30 / odcloud 401), 신청 직후 반영됐다.

| 서버 | data.go.kr 데이터셋 | 결과 |
|---|---|---|
| nps-business-enrollment | [3046071](https://www.data.go.kr/data/3046071/openapi.do) 국민연금공단_국민연금 가입 사업장 내역 | `resultCode 00`, 실데이터 |
| nts-business-verification | 국세청_사업자등록정보 진위확인 및 상태조회 (odcloud) | `status_code OK`, 실데이터 |
| pps-narajangteo | 조달청_나라장터 공공데이터개방표준서비스 | `resultCode 00`, 최근 1주 범위로 입찰공고 반환 |
| fsc-financial-info | [15043459](https://www.data.go.kr/data/15043459/openapi.do) 금융위원회_기업 재무정보 | `resultCode 00`, 실데이터 |
| presidential-speeches | [15084167](https://www.data.go.kr/data/15084167/fileData.do) 대통령기록관_대통령연설기록(연설문) | 두 UDDI(`1c8b5454…`, `f30c6ace…`) 모두 200 |
| msds-chemical-info | 안전보건공단 MSDS (`msds.kosha.or.kr`, 포털 외부) | `resultCode 00`, XML — **data.go.kr 키 그대로 사용 가능** |

## 개발

```bash
uv sync --dev --all-packages
uv run pytest
uv run python -m data_go_mcp.nps_business_enrollment.server   # 서버 단독 실행
```

## 요구사항

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- data.go.kr API 키 (`API_KEY` 환경변수)

## 라이선스

Apache-2.0. 원저작물의 저작권 표시는 [LICENSE](LICENSE) 및 각 패키지에 유지한다.
