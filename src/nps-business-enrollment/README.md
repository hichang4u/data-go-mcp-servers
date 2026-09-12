# data-go-mcp.nps-business-enrollment

국민연금공단 사업장 가입내역 + 행정안전부 법정동코드 + 근로복지공단 고용·산재보험 현황 MCP 서버 (API 3종, 각각 활용신청 필요). 툴 레퍼런스·예시·제약은 [docs/guide/servers/nps-business-enrollment.md](../../docs/guide/servers/nps-business-enrollment.md).

## 실행

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nps-business-enrollment" data-go-mcp.nps-business-enrollment
```

환경변수 `API_KEY` (또는 `NPS_BUSINESS_ENROLLMENT_API_KEY`) 에 data.go.kr 인증키. 클라이언트 설정은 [docs/guide/installation.md](../../docs/guide/installation.md), 키 발급·활용신청은 [docs/guide/api-keys.md](../../docs/guide/api-keys.md).

## 개발

```bash
uv run pytest src/nps-business-enrollment/tests -q
uv run python -m data_go_mcp.nps_business_enrollment.server
```

패키지 구조: `data_go_mcp/nps_business_enrollment/{api_client,models,server}.py`. 공통 코드는 `data-go-mcp-core`.
