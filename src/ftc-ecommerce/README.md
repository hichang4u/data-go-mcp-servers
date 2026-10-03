# data-go-mcp.ftc-ecommerce

공정거래위원회 통신판매사업자 등록상세를 MCP 로 제공한다. 사업자등록번호 하나로 온라인 판매 신고 내역을 조회한다.

```bash
uvx --from "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/ftc-ecommerce" data-go-mcp.ftc-ecommerce
```

환경변수 `API_KEY` (또는 `FTC_ECOMMERCE_API_KEY`). [활용신청](https://www.data.go.kr/data/15126315/openapi.do)이 필요하다.

| 툴 | 하는 일 |
|---|---|
| `get_online_seller` | 통신판매업 신고 내역 (사업자번호 또는 신고번호) |

사용법과 함정은 [docs/guide/servers/ftc-ecommerce.md](../../docs/guide/servers/ftc-ecommerce.md).
