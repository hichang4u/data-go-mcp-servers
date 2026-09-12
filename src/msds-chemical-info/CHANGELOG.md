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
- 환경변수: `API_KEY` 에 더해 서버별 `MSDS_CHEMICAL_INFO_API_KEY` 가 우선
- 로그는 stderr 로만. API 키 없이도 서버가 기동되며 툴 호출 시 오류
- 엔드포인트를 `https` 로
- 테스트 전면 재작성 (respx + 인프로세스 `mcp.Client`, 실응답 fixture)

### Fixed
- XML 파싱을 `ElementTree` 에서 core(xmltodict) 로. 빈 요소가 있어도 한 행 때문에 툴이 실패하지 않음
- 섹션 묶음 툴과 `get_complete_msds` 가 섹션을 동시에 조회 (16섹션 약 0.6초). 실패한 섹션은 `error` 를 담고 나머지는 반환
- `detect_search_type` 이 모듈 함수로, CAS/EN 판별 강화


## [0.1.0] - 2025-09-17

### Added
- Initial release of MSDS Chemical Info MCP server
- Basic API client implementation
- Core MCP tools for accessing 물질안전보건자료(MSDS) API