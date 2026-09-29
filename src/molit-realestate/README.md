# 국토교통부 부동산 실거래가 MCP Server

아파트·오피스텔·연립다세대·단독다가구·상업업무용·토지의 신고된 실거래가를 MCP 로 제공한다 (매매 6종, 전월세 4종).

사용자 문서: [docs/guide/servers/molit-realestate.md](../../docs/guide/servers/molit-realestate.md)

## 실행

```bash
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/molit-realestate" data-go-mcp.molit-realestate
```

환경변수 `API_KEY` (data.go.kr 공통 인증키). 부동산 종류마다 활용신청이 따로 필요하다.

## 툴

| 툴 | 하는 일 |
|---|---|
| `search_property_trades` | 매매 실거래가 (아파트/오피스텔/연립다세대/단독다가구/상업업무용/토지) |
| `search_property_rents` | 전월세 실거래가 (아파트/오피스텔/연립다세대/단독다가구) |

지역코드는 nps 서버의 `find_region_code` 로 찾는다.
