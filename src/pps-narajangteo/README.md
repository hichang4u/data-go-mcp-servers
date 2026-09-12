# data-go-mcp.pps-narajangteo

조달청 나라장터 입찰·낙찰·계약 MCP 서버. 툴 레퍼런스·예시·제약은 [docs/guide/servers/pps-narajangteo.md](../../docs/guide/servers/pps-narajangteo.md).

## 실행

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/pps-narajangteo" data-go-mcp.pps-narajangteo
```

환경변수 `API_KEY` (또는 `PPS_NARAJANGTEO_API_KEY`) 에 data.go.kr 인증키. 클라이언트 설정은 [docs/guide/installation.md](../../docs/guide/installation.md), 키 발급·활용신청은 [docs/guide/api-keys.md](../../docs/guide/api-keys.md).

## 개발

```bash
uv run pytest src/pps-narajangteo/tests -q
uv run python -m data_go_mcp.pps_narajangteo.server
```

패키지 구조: `data_go_mcp/pps_narajangteo/{api_client,models,server}.py`. 공통 코드는 `data-go-mcp-core`.
