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
- 환경변수: `API_KEY` 에 더해 서버별 `PPS_NARAJANGTEO_API_KEY` 가 우선
- 로그는 stderr 로만. API 키 없이도 서버가 기동되며 툴 호출 시 오류
- 엔드포인트를 `https` 로
- 테스트 전면 재작성 (respx + 인프로세스 `mcp.Client`, 실응답 fixture)

### Fixed
- `get_bid_detail`: 공고번호 단건 조회 API 가 없어 기간을 훑는 구조였는데 API 범위 제한(1개월)과 맞지 않아 동작하지 않았다. 30일 창을 999건×3페이지 검색하고 `start_date`/`end_date` 로 좁힐 수 있게 수정. 못 찾으면 오류.
- `xmltodict` 의존성 제거 (JSON 만 사용)


## [0.1.0] - 2025-08-29

### Added
- Initial release of Weather Forecast MCP server
- Basic API client implementation
- Core MCP tools for accessing 기상청 날씨 예보 API