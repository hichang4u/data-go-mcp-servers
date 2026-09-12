# data-go-mcp.msds-chemical-info

안전보건공단 MSDS 화학물질 정보 MCP 서버. 툴 레퍼런스·예시·제약은 [docs/guide/servers/msds-chemical-info.md](../../docs/guide/servers/msds-chemical-info.md).

## 실행

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/msds-chemical-info" data-go-mcp.msds-chemical-info
```

환경변수 `API_KEY` (또는 `MSDS_CHEMICAL_INFO_API_KEY`) 에 data.go.kr 인증키. 클라이언트 설정은 [docs/guide/installation.md](../../docs/guide/installation.md), 키 발급·활용신청은 [docs/guide/api-keys.md](../../docs/guide/api-keys.md).

## 개발

```bash
uv run pytest src/msds-chemical-info/tests -q
uv run python -m data_go_mcp.msds_chemical_info.server
```

패키지 구조: `data_go_mcp/msds_chemical_info/{api_client,models,server}.py`. 공통 코드는 `data-go-mcp-core`.
