# Changelog

## [0.1.1] - 2026-09-13

### Fixed
- `BaseDataGoClient._gateway_error`: XML 서비스(`response_format="xml"`)에서 게이트웨이 오류(`OpenAPI_ServiceResponse`)가 XML 로, 때로는 HTTP 200 으로 오는 경우도 `DataGoAPIError` 로 매핑. 이전에는 `HTTP 403: <?xml …` 또는 빈 결과로 새어 나갔다.

## [0.1.0] - 2026-09-12

- 최초 릴리스: `BaseDataGoClient`, `DataGoAPIError`, `load_api_key`, `tool_errors`, `READ_ONLY`, `configure_logging`, `parse_xml_response`
