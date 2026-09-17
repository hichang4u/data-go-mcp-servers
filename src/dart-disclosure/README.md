# data-go-mcp.dart-disclosure

금융감독원 전자공시 DART(OpenDART) MCP 서버 — 기업 개황, 공시 목록·원문, 정기보고서 재무제표. 툴 레퍼런스·예시·제약은 [docs/guide/servers/dart-disclosure.md](../../docs/guide/servers/dart-disclosure.md).

## 실행

```
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/dart-disclosure" data-go-mcp.dart-disclosure
```

환경변수 `DART_DISCLOSURE_API_KEY` 에 [opendart.fss.or.kr](https://opendart.fss.or.kr) 인증키. data.go.kr 키(`API_KEY`)는 쓰이지 않는다. 클라이언트 설정은 [docs/guide/installation.md](../../docs/guide/installation.md), 키 발급은 [docs/guide/api-keys.md](../../docs/guide/api-keys.md) 4절.

## 개발

```bash
uv run pytest src/dart-disclosure/tests -q
uv run python -m data_go_mcp.dart_disclosure.server
uv run python scripts/harvest_dart_corp_codes.py   # 기업코드 스냅샷 갱신 (릴리스 전)
```

패키지 구조: `data_go_mcp/dart_disclosure/{api_client,models,server,corp_codes}.py` + `corp_codes.json.gz`(기업코드 스냅샷, 약 1.5MB). 공통 코드는 `data-go-mcp-core`.
