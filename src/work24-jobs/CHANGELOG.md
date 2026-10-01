# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-01

### Added
- 고용24 채용정보 서버 첫 릴리스 — 툴 2개 (`search_job_postings`, `get_job_posting`)
- 사업자등록번호로 공고가 직접 필터된다 (기간 훑기가 필요 없다)
- 지역코드는 법정동코드 앞 5자리와 호환 — nps `find_region_code` 결과를 그대로 받는다
- 오류 래핑 두 가지 처리: `GO24.error`(미신청 서비스)와 `wantedRoot.messageCd`.
  `006`(결과 없음)은 목록에선 빈 결과, 상세에선 오류로 올린다
- 결과가 하나일 때 XML 이 리스트가 아닌 단일 요소로 오는 것을 처리
- Core MCP tools for accessing 고용24 채용정보 API