# data-go-mcp.nts-business-verification

국세청 사업자등록정보 진위확인·상태조회 MCP 서버. 툴 레퍼런스·예시·제약은 [docs/guide/servers/nts-business-verification.md](../../docs/guide/servers/nts-business-verification.md).

## 실행

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nts-business-verification" data-go-mcp.nts-business-verification
```

환경변수 `API_KEY` (또는 `NTS_BUSINESS_VERIFICATION_API_KEY`) 에 data.go.kr 인증키. 클라이언트 설정은 [docs/guide/installation.md](../../docs/guide/installation.md), 키 발급·활용신청은 [docs/guide/api-keys.md](../../docs/guide/api-keys.md).

## 개발

```bash
uv run pytest src/nts-business-verification/tests -q
uv run python -m data_go_mcp.nts_business_verification.server
```

패키지 구조: `data_go_mcp/nts_business_verification/{api_client,models,server}.py`. 공통 코드는 `data-go-mcp-core`.
