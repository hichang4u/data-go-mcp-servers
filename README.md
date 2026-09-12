# data-go-mcp-servers

한국 공공데이터 API 를 MCP(Model Context Protocol) 서버로 제공한다. Claude Desktop, Claude Code 등 MCP 클라이언트에서 국민연금 사업장, 사업자등록 상태, 나라장터 입찰, 기업 재무제표, 대통령 연설문, MSDS 화학물질 정보를 바로 조회할 수 있다.

[Koomook/data-go-mcp-servers](https://github.com/Koomook/data-go-mcp-servers)(Apache-2.0, 2025-09 이후 정지)를 기반으로 mcp SDK 2.x 에 맞춰 재정비한 것이다. 툴 이름과 파라미터는 원저장소와 호환된다.

## 서버

| 서버 | 기관 / 데이터 | 툴 |
|---|---|---|
| [nps-business-enrollment](docs/guide/servers/nps-business-enrollment.md) | 국민연금공단 — 사업장 가입내역 (+ 법정동코드 조회) | `search_business` `get_business_detail` `get_period_status` `find_region_code` |
| [nts-business-verification](docs/guide/servers/nts-business-verification.md) | 국세청 — 사업자등록 진위확인·상태 | `validate_business` `check_business_status` `batch_validate_businesses` |
| [pps-narajangteo](docs/guide/servers/pps-narajangteo.md) | 조달청 — 나라장터 입찰·낙찰·계약 | `search_bid_announcements` `search_successful_bids` `search_contracts` `get_bid_detail` |
| [fsc-financial-info](docs/guide/servers/fsc-financial-info.md) | 금융위원회 — 기업 재무제표 | `get_summary_financial_statement` `get_balance_sheet` `get_income_statement` `search_company_financial_info` |
| [presidential-speeches](docs/guide/servers/presidential-speeches.md) | 대통령기록관 — 연설문 | `list_speeches` `search_speeches` `get_recent_speeches` |
| [msds-chemical-info](docs/guide/servers/msds-chemical-info.md) | 안전보건공단 — MSDS | `search_chemicals` `get_chemical_section` `get_complete_msds` 외 4 |

모든 툴은 조회 전용이며, 실패는 MCP 오류 결과(`isError`)로 전달된다.

## 빠른 시작

1. [uv](https://docs.astral.sh/uv/getting-started/installation/) 설치
2. [data.go.kr](https://www.data.go.kr) 인증키(Decoding) 발급 후 쓰려는 API 에 **활용신청** → [docs/guide/api-keys.md](docs/guide/api-keys.md)
3. Claude Desktop 설정(`claude_desktop_config.json`)에 추가:

```json
{
  "mcpServers": {
    "nts-business-verification": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nts-business-verification",
        "data-go-mcp.nts-business-verification"
      ],
      "env": { "API_KEY": "<data.go.kr 인증키>" }
    }
  }
}
```

다른 서버는 `nts-business-verification` 을 서버명으로 바꾸면 된다. Claude Code, Cline, clone 해서 쓰는 방법은 [docs/guide/installation.md](docs/guide/installation.md).

```
> 사업자등록번호 120-88-00767 상태 조회해줘
계속사업자, 부가가치세 일반과세자 …
```

## 문서

| | |
|---|---|
| 사용 | [설치·클라이언트 설정](docs/guide/installation.md) · [API 키·활용신청](docs/guide/api-keys.md) · [문제 해결](docs/guide/troubleshooting.md) · [서버별 툴 레퍼런스](docs/guide/servers/) |
| 개발 | [CONTRIBUTING](CONTRIBUTING.md) · [아키텍처](docs/development/architecture.md) · [새 서버 추가](docs/development/adding-a-server.md) · [테스트](docs/development/testing.md) · [릴리스](docs/development/release.md) |
| 이력 | [PRD](docs/development/PRD.md) · [작업 계획](docs/development/PLAN.md) · [원저장소 기록](docs/history/) |

## 개발

```bash
git clone https://github.com/hichang4u/data-go-mcp-servers && cd data-go-mcp-servers
uv sync --dev --all-packages
uv run pytest                                   # 207 tests; 실호출은 .env 에 API_KEY 를 두고 -m integration
uv run ruff check src scripts tests && uv run pyright src scripts tests
uv run python scripts/check_apis.py             # 7개 API 생존·권한 확인
```

Python 3.10+, `mcp>=2.2`. CI 는 ubuntu/windows × 3.10/3.13 에서 pytest, ruff, pyright 를 필수로 돌린다.

## 라이선스

Apache-2.0. 원저작물 저작권 표시는 [LICENSE](LICENSE) 와 각 패키지에 유지한다. 이 프로젝트는 data.go.kr 및 각 기관과 무관하며, 데이터 이용은 각 API 의 이용약관을 따른다.
