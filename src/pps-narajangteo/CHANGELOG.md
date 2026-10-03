# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-10-03

### Added
- `get_procurement_company` — 조달 등록업체 기본정보·등록업종·공급물품 (사업자번호 하나로)
- `check_procurement_sanctions` — 부정당업자 제재 이력. `restricted_now` 로 현재 제한 여부를 따로 준다
- 두 툴 모두 API 총계(`industry_count`·`product_count`·`total_count`)와 `complete` 를 준다 — 한 번에 100건까지만 받기 때문

사용자정보서비스(`ao/UsrInfoService02`)는 낙찰정보와 달리 사업자번호 필터가 실제로 동작한다.
오퍼레이션마다 "사업자등록번호 기준검색"의 `inqryDiv` 가 다르다 (기본정보 3, 나머지 1).

## [0.6.1] - 2026-10-01

### Fixed
- `find_bid_winners` 가 기본 30초 타임아웃으로 돌아, 999건짜리 페이지 하나가 느리면 스캔 전체가
  `네트워크 오류` 로 끊기던 문제 — 90초로

## [0.6.0] - 2026-09-30

### Added
- `find_bid_winners` — 사업자번호·업체명으로 낙찰 이력 조회. 나라장터 API 가 업체 필터를 무시하므로
  기간(기본 1개월, 최대 3개월)을 999건씩 훑어 거른다. 낙찰정보서비스(`as/ScsbidInfoService`) 사용.
  API 한도가 한 요청에 1개월이라 달 단위로 나눠 호출하고, 다 훑지 못하면 `complete: false` 로 알린다

## [0.5.0] - 2026-09-20

### Changed
- `search_contracts`: 실제 API 한도는 7일 (8일부터 07) — 초과 시 `입력값 오류` 로 먼저 막는다. 설명의 "1개월" 정정
- `search_successful_bids`: 기본 조회일을 오늘에서 **직전 평일**로 (당일 개찰은 불완전)
- `get_bid_detail`: 기본 범위 30일 → 7일, 스캔 3페이지 → 12페이지 (하루 1,100건 이상이라 30일은 못 훑었다)

## [0.4.0] - 2026-09-20

### Fixed
- API 오류가 `response` 가 아니라 `nkoneps.com.response.ResponseError` 로 오는 것을 놓쳐 "성공, 0건" 으로 보이던 문제 — 이제 `DataGoAPIError` 로 전달 (`[07] 입력범위값 초과 에러` 등)
- `search_successful_bids`: 낙찰 API 의 조회 범위는 실제로 하루라(이틀부터 07) 기본 7일 조회가 항상 실패하던 문제. 기본은 오늘(주말이면 직전 금요일), 여러 날을 넘기면 `입력값 오류`

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