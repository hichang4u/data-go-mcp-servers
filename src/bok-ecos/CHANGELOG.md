# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-09-29

### Fixed
- `sample` 키로 호출할 때 툴 기본 건수(100/200)가 그대로 나가 `ERROR-301` 이 나던 문제 — 10건으로 제한
- 통계표 목록 캐시가 동시 호출 시 두 배가 되던 문제 (락 + 대입)
- `list_total_count` 가 없는 응답에서 첫 페이지만 캐시하던 문제
- 항목 코드 앞자리를 비우면 뒤 코드가 앞으로 밀려 다른 값이 오던 문제 — 입력값 오류로 막는다

## [0.1.0] - 2026-09-29

### Added
- 한국은행 ECOS 서버 첫 릴리스 — 툴 5개 (`find_statistic_table`, `get_statistic_items`,
  `get_statistic_data`, `get_key_statistics`, `search_term`)
- 인증키가 경로 세그먼트인 ECOS 규격과 `RESULT` 오류 래핑 처리. `INFO-200`(자료 없음)은 빈 결과
- 주기별 시점 형식 검증 (년 2024, 분기 2024Q1, 월 202401, 일 20240115)
- Core MCP tools for accessing 한국은행 경제통계시스템(ECOS) API