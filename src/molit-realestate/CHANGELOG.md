# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-01

### Added
- `get_building_register` — 건축HUB 건축물대장 (표제부·층별개요·지역지구 등 8종). 실거래의 본번·부번으로 바로 이어진다
- 실거래 결과에 `bun`·`ji` 노출 (건축물대장 조회 열쇠)
- 이 API 가 자주 내는 `SERVICETIMEOUT_ERROR` 는 세 번까지 재시도

## [0.1.0] - 2026-09-30

### Added
- 국토교통부 실거래가 서버 첫 릴리스 — 툴 2개 (`search_property_trades`, `search_property_rents`)
- 부동산 종류 11개 API 를 종류 파라미터 하나로 묶었다 (매매 7종, 전월세 4종)
- 법정동코드 10자리를 받아 앞 5자리로 정규화 (nps `find_region_code` 결과를 그대로 쓸 수 있다)
- 잘못된 입력을 API 가 0건으로 삼키기 전에 형식 검증으로 막는다 (시도 단위 코드 포함). 정상 코드가 `000` 인 것도 처리
- Core MCP tools for accessing 국토교통부 부동산 실거래가 API