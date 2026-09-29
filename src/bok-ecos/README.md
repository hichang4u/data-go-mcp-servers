# 한국은행 ECOS MCP Server

한국은행 경제통계시스템(ECOS)의 거시 경제통계를 MCP 로 제공한다 — 기준금리·환율·물가, 100대 통계지표, 통계 시계열.

사용자 문서: [docs/guide/servers/bok-ecos.md](../../docs/guide/servers/bok-ecos.md)

## 실행

```bash
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/bok-ecos" data-go-mcp.bok-ecos
```

환경변수 `BOK_ECOS_API_KEY` ([ecos.bok.or.kr](https://ecos.bok.or.kr) 에서 발급, 즉시). data.go.kr 의 공통 `API_KEY` 는 쓰이지 않는다. 시험용으로 `sample` 을 넣으면 한 번에 10건까지 조회된다.

## 툴

| 툴 | 하는 일 |
|---|---|
| `find_statistic_table` | 통계표 코드를 이름으로 찾기 |
| `get_statistic_items` | 통계표의 세부항목·주기별 조회 가능 기간 |
| `get_statistic_data` | 통계 시계열 조회 |
| `get_key_statistics` | 100대 통계지표 최신값 |
| `search_term` | 통계 용어 설명 |
