# Changelog

## [0.2.0] - 2026-09-17

### Added
- `BaseDataGoClient.shared_key` (기본 `True`) — `False` 면 `load_api_key` 가 공통 `API_KEY` 를 보지 않는다. data.go.kr 키로는 호출이 안 되는 포털(OpenDART)용. `key_url` 로 키 발급처 안내 문구를 바꾼다.
- `DataGoAPIError(source=)` — `tool_errors` 의 오류 접두어(`data.go.kr 오류`)를 제공처에 맞게 바꾼다 (`OpenDART 오류 [013] …`).

## [0.1.1] - 2026-09-13

### Fixed
- `BaseDataGoClient._gateway_error`: XML 서비스(`response_format="xml"`)에서 게이트웨이 오류(`OpenAPI_ServiceResponse`)가 XML 로, 때로는 HTTP 200 으로 오는 경우도 `DataGoAPIError` 로 매핑. 이전에는 `HTTP 403: <?xml …` 또는 빈 결과로 새어 나갔다.

## [0.1.0] - 2026-09-12

- 최초 릴리스: `BaseDataGoClient`, `DataGoAPIError`, `load_api_key`, `tool_errors`, `READ_ONLY`, `configure_logging`, `parse_xml_response`
