# data-go-mcp.presidential-speeches

대통령기록관 연설문 MCP 서버. 툴 레퍼런스·예시·제약은 [docs/guide/servers/presidential-speeches.md](../../docs/guide/servers/presidential-speeches.md).

## 실행

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/presidential-speeches" data-go-mcp.presidential-speeches
```

환경변수 `API_KEY` (또는 `PRESIDENTIAL_SPEECHES_API_KEY`) 에 data.go.kr 인증키. 클라이언트 설정은 [docs/guide/installation.md](../../docs/guide/installation.md), 키 발급·활용신청은 [docs/guide/api-keys.md](../../docs/guide/api-keys.md).

## 개발

```bash
uv run pytest src/presidential-speeches/tests -q
uv run python -m data_go_mcp.presidential_speeches.server
```

패키지 구조: `data_go_mcp/presidential_speeches/{api_client,models,server}.py`. 공통 코드는 `data-go-mcp-core`.
