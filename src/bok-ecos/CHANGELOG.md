# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-29

### Added
- 한국은행 ECOS 서버 첫 릴리스 — 툴 5개 (`find_statistic_table`, `get_statistic_items`,
  `get_statistic_data`, `get_key_statistics`, `search_term`)
- 인증키가 경로 세그먼트인 ECOS 규격과 `RESULT` 오류 래핑 처리. `INFO-200`(자료 없음)은 빈 결과
- 주기별 시점 형식 검증 (년 2024, 분기 2024Q1, 월 202401, 일 20240115)
- Core MCP tools for accessing 한국은행 경제통계시스템(ECOS) API