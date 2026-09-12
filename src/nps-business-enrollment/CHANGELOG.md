# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-09-13

### Added
- `get_insurance_status`: 사업자등록번호(10자리)로 고용·산재보험 가입 사업장 현황 (상시인원, 성립일, 업종, 주소, 종류별 `summary`). 근로복지공단_고용/산재보험 현황정보 API (`gySjbPstateInfoService`, XML, 별도 활용신청 필요).

## [0.4.0] - 2026-09-12

### Added
- `find_region_code`: 지역명 → 법정동코드 (행정안전부 행정표준코드 `StanReginCd`). 결과의 `nps_params` 를 `search_business` 에 그대로 넘길 수 있다. 이 API 도 별도 활용신청이 필요하다.

### Fixed
- `search_business` 지역 코드 설명을 실제 형식(시도 2자리 / 시군구 3자리 / 읍면동 3자리)으로 바로잡음. 이전 설명(5자리/8자리)대로 넣으면 결과가 0건이었다.

## [0.3.0] - 2026-09-12

### Changed
- mcp SDK 2.x (`mcp>=2.2,<3`) 로 이전: `FastMCP` → `MCPServer`
- 공통 패키지 `data-go-mcp-core` 위로 이전 (`BaseDataGoClient`, `DataGoAPIError`, `load_api_key`)
- 툴 실패는 `{"error": ...}` dict 대신 MCP 오류 결과(`isError`)로 전달 (`ToolError`)
- 모든 툴에 `readOnlyHint`/`openWorldHint` annotation 과 파라미터 설명(`Field(description=)`)
- 환경변수: `API_KEY` 에 더해 서버별 `NPS_BUSINESS_ENROLLMENT_API_KEY` 가 우선
- 로그는 stderr 로만. API 키 없이도 서버가 기동되며 툴 호출 시 오류
- 엔드포인트를 `https` 로
- 테스트 전면 재작성 (respx + 인프로세스 `mcp.Client`, 실응답 fixture)


## [0.2.0] - 2025-01-28

### Changed
- **BREAKING CHANGE**: Unified API key environment variable from `NPS_API_KEY` to `API_KEY`
- All data.go.kr MCP servers now use a single `API_KEY` environment variable
- Updated documentation to reflect the unified API key approach

### Migration Guide
If you're upgrading from v0.1.0:
1. Change your environment variable from `NPS_API_KEY` to `API_KEY`
2. Update your Claude Desktop configuration to use `API_KEY` instead of `NPS_API_KEY`

## [0.1.0] - 2025-01-28

### Added
- Initial release of NPS Business Enrollment MCP Server
- `search_business` tool for searching National Pension Service business enrollment data
- Support for searching by:
  - Administrative district codes (시도, 시군구, 읍면동)
  - Business name
  - Business registration number (first 6 digits)
- Pagination support (page_no, num_of_rows)
- Comprehensive error handling
- Full documentation and examples