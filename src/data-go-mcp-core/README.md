# data-go-mcp-core

`data-go-mcp.*` 서버들이 공유하는 코드.

- `data_go_mcp.core.keys` — `load_api_key(prefix)`: `<PREFIX>_API_KEY` 우선, 없으면 `API_KEY`
- `data_go_mcp.core.errors` — `DataGoAPIError`, `RESULT_CODES`
- `data_go_mcp.core.client` — `BaseDataGoClient`, `to_camel`, `normalize_items`
- `data_go_mcp.core.xml` — `parse_xml_response` (extra `xml`)
- `data_go_mcp.core.logging` — `configure_logging()`: stderr 전용
