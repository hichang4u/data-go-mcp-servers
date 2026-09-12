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
- 환경변수: `API_KEY` 에 더해 서버별 `PRESIDENTIAL_SPEECHES_API_KEY` 가 우선
- 로그는 stderr 로만. API 키 없이도 서버가 기동되며 툴 호출 시 오류
- 엔드포인트를 `https` 로
- 테스트 전면 재작성 (respx + 인프로세스 `mcp.Client`, 실응답 fixture)

### Fixed
- `search_speeches`: 현재 페이지 10건만 클라이언트에서 거르던 것을 odcloud `cond[컬럼::EQ|LIKE]` 서버측 필터로 교체. `total_count` 는 조건에 맞는 전체 건수
- `get_recent_speeches`: 목록이 오래된 순이라 1948년 연설을 돌려주던 버그 수정 — 건수를 확인해 마지막 페이지를 읽고 최신순 반환. 마지막 페이지가 짧으면 앞 페이지에서 채움. `limit < 1` 은 오류


## [0.1.0] - 2025-08-28

### Added
- Initial release of Presidential Speech Records MCP server
- Basic API client implementation
- Core MCP tools for accessing 대통령기록관 연설문 API