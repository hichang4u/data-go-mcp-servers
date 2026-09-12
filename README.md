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
| nps-business-enrollment | 국민연금공단 사업장 가입내역 | 예정 |
| nts-business-verification | 국세청 사업자등록정보 진위확인·상태조회 | 예정 |
| pps-narajangteo | 조달청 나라장터 입찰·낙찰·계약 | 예정 |
| fsc-financial-info | 금융위원회 기업 재무정보 | 예정 |
| presidential-speeches | 대통령기록관 연설문 | 예정 |
| msds-chemical-info | 안전보건공단 MSDS 화학물질 정보 | 예정 |

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

## 현재 상태 (Phase 0 기준선, 2026-09-12)

원본 코드를 `src/`에 그대로 가져온 뒤 루트 `pyproject.toml`에 `constraint-dependencies = ["mcp<2"]`
임시 핀을 걸어 측정했다.

| 항목 | 결과 |
|---|---|
| `uv run pytest` | 59 passed, 3 failed (fsc 2, nps 1 — 원본부터 깨져 있던 테스트) |
| `ruff check src scripts` | 917건 (795건 자동 수정 가능) |
| `pyright src` | 46 errors |

기준선을 잡기 위해 원본에서 두 가지를 바꿨다.

- `src/fsc-financial-info/data_go_mcp/__init__.py` 삭제 — 이 파일 때문에 `data_go_mcp`가
  일반 패키지로 잡혀 같은 환경에 두 서버 이상 설치하면 다른 서버 모듈을 import 못 했다.
- pytest `--import-mode=importlib` — 서버마다 `test_api.py` 같은 basename을 쓰고 있어 루트에서
  한 번에 돌리면 충돌했다.

API 생존 확인: `API_KEY=... uv run python scripts/check_apis.py`

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
