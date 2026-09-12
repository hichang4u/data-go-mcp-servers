# data-go-mcp.fsc-financial-info

금융위원회 기업 재무정보 + 기업기본정보(법인번호·개요) + 주식시세 MCP 서버 (API 3종, 각각 활용신청 필요). 툴 레퍼런스·예시·제약은 [docs/guide/servers/fsc-financial-info.md](../../docs/guide/servers/fsc-financial-info.md).

## 실행

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/fsc-financial-info" data-go-mcp.fsc-financial-info
```

환경변수 `API_KEY` (또는 `FSC_FINANCIAL_INFO_API_KEY`) 에 data.go.kr 인증키. 클라이언트 설정은 [docs/guide/installation.md](../../docs/guide/installation.md), 키 발급·활용신청은 [docs/guide/api-keys.md](../../docs/guide/api-keys.md).

## 개발

```bash
uv run pytest src/fsc-financial-info/tests -q
uv run python -m data_go_mcp.fsc_financial_info.server
```

패키지 구조: `data_go_mcp/fsc_financial_info/{api_client,models,server}.py`. 공통 코드는 `data-go-mcp-core`.
