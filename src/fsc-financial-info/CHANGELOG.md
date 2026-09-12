# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-09-12

### Changed
- mcp SDK 2.x (`mcp>=2.2,<3`) 로 이전: `FastMCP` → `MCPServer`
- 공통 패키지 `data-go-mcp-core` 위로 이전 (`BaseDataGoClient`, `DataGoAPIError`, `load_api_key`)
- 툴 실패는 `{"error": ...}` dict 대신 MCP 오류 결과(`isError`)로 전달 (`ToolError`)
- 모든 툴에 `readOnlyHint`/`openWorldHint` annotation 과 파라미터 설명(`Field(description=)`)
- 환경변수: `API_KEY` 에 더해 서버별 `FSC_FINANCIAL_INFO_API_KEY` 가 우선
- 로그는 stderr 로만. API 키 없이도 서버가 기동되며 툴 호출 시 오류
- 엔드포인트를 `https` 로
- 테스트 전면 재작성 (respx + 인프로세스 `mcp.Client`, 실응답 fixture)

### Fixed
- 저수준 `mcp.server.Server` 에서 `MCPServer` 로 재작성 (mcp 2.x 에서 데코레이터 API 제거). 툴 이름·파라미터·출력 문구 동일
- `ERROR_CODES` 표는 core 의 `RESULT_CODES` 로 이동, `parse_decimal` 은 모듈 함수
- 모델 JSON 직렬화: `json_encoders` → 금액 필드 `JsonDecimal`
- `xmltodict` 의존성 제거


## [0.2.0] - 2025-01-28

### Changed
- **BREAKING CHANGE**: Unified API key environment variable from `FSC_FINANCIAL_INFO_API_KEY` to `API_KEY`
- All data.go.kr MCP servers now use a single `API_KEY` environment variable
- Updated documentation to reflect the unified API key approach

### Migration Guide
If you're upgrading from v0.1.x:
1. Change your environment variable from `FSC_FINANCIAL_INFO_API_KEY` to `API_KEY`
2. Update your Claude Desktop configuration to use `API_KEY` instead of `FSC_FINANCIAL_INFO_API_KEY`

## [0.1.1] - Previous Release

### Added
- Initial release of FSC Financial Info MCP server
- Summary financial statements retrieval
- Balance sheet data access
- Income statement data access
- Comprehensive financial search functionality