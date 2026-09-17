# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-17

### Added
- 최초 릴리스. OpenDART 6개 엔드포인트: `find_corp_code`(동봉 기업코드 스냅샷 검색, API 호출 없음), `get_company`, `list_disclosures`, `get_key_accounts`, `get_financial_statements`, `get_disclosure_document`(원문 HTML → 텍스트, offset 페이징)
- 기업코드 스냅샷 `corp_codes.json.gz` (119,352개사, 2026-09-17). 갱신: `scripts/harvest_dart_corp_codes.py`
- 키는 `DART_DISCLOSURE_API_KEY` 만 (data.go.kr `API_KEY` fallback 없음, core 0.2.0 의 `shared_key=False`)
