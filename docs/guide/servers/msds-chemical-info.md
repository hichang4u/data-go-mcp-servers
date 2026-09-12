# 안전보건공단 MSDS 화학물질 정보 (msds-chemical-info)

화학물질을 국문명·CAS/UN/KE/EN 번호로 찾고, 물질안전보건자료(MSDS) 16개 섹션(유해성, 응급조치, 취급·저장, 물리화학적 특성, 독성, 법적 규제 등)을 조회한다.

| | |
|---|---|
| 데이터셋 | 안전보건공단 물질안전보건자료(MSDS) — `msds.kosha.or.kr/openapi` (포털 게이트웨이를 거치지 않는 직접 호출) |
| 활용신청 | data.go.kr 에서 발급한 키 그대로 사용 가능 (별도 신청 불필요, 2026-09 확인) |
| 환경변수 | `API_KEY` 또는 `MSDS_CHEMICAL_INFO_API_KEY` |
| 패키지 | `data-go-mcp.msds-chemical-info` (`src/msds-chemical-info`) |

## 설정

```json
"msds-chemical-info": {
  "command": "uvx",
  "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/msds-chemical-info", "data-go-mcp.msds-chemical-info"],
  "env": { "API_KEY": "<data.go.kr 인증키>" }
}
```

## 예시 프롬프트

- "벤젠의 MSDS 정보를 찾아줘"
- "CAS 71-43-2 의 유해성·위험성과 응급조치 요령"
- "UN1114 취급 및 저장 방법"
- "chem_id 001008 의 전체 MSDS"

## 알아둘 것

- 검색 구분은 검색어 형태로 자동 감지된다 (`71-43-2` → CAS, `UN1114`/`1114` → UN, `KE-02150` → KE, `200-753-7` → EN, 그 외 국문명). 필요하면 `search_type` 으로 지정.
- 상세 조회 키는 `chem_id`(6자리). 짧게 주면 앞을 0으로 채운다.
- 섹션 묶음 툴은 4개 섹션을, `get_complete_msds` 는 16개 섹션을 **동시에** 호출한다. 일부 섹션이 실패하면 해당 섹션에 `error` 를 넣고 나머지는 돌려준다.
- 응답 원문은 XML 이며 서버가 JSON 으로 바꿔 준다. 값이 없는 항목은 "자료없음".

## 툴

<!-- tools:start -->

### `get_chemical_handling_info`

화학물질의 취급·보호 정보를 조회합니다 (섹션 5-8: 화재, 누출, 취급·저장, 보호구).

Get handling and protection information (sections 5-8).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `chem_id` | string | 예 |  | 화학물질ID 6자리 (search_chemicals 결과의 chem_id; 짧으면 0으로 채움) |

### `get_chemical_properties`

화학물질의 물성·독성 정보를 조회합니다 (섹션 9-12: 물리화학적 특성, 안정성, 독성, 환경).

Get physical/chemical properties and toxicity (sections 9-12).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `chem_id` | string | 예 |  | 화학물질ID 6자리 (search_chemicals 결과의 chem_id; 짧으면 0으로 채움) |

### `get_chemical_regulatory_info`

화학물질의 규제·폐기 정보를 조회합니다 (섹션 13-16: 폐기, 운송, 법적 규제, 기타).

Get regulatory and disposal information (sections 13-16).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `chem_id` | string | 예 |  | 화학물질ID 6자리 (search_chemicals 결과의 chem_id; 짧으면 0으로 채움) |

### `get_chemical_safety_summary`

화학물질의 핵심 안전정보를 조회합니다 (섹션 1-4: 제품·회사, 유해성, 구성성분, 응급조치).

Get essential safety information (sections 1-4).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `chem_id` | string | 예 |  | 화학물질ID 6자리 (search_chemicals 결과의 chem_id; 짧으면 0으로 채움) |

### `get_chemical_section`

화학물질 MSDS 의 특정 섹션을 조회합니다. Get one MSDS section (1-16).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `chem_id` | string | 예 |  | 화학물질ID 6자리 (search_chemicals 결과의 chem_id; 짧으면 0으로 채움) |
| `section_number` | integer | 예 |  | 섹션 번호 1-16:<br>1: 화학제품과 회사에 관한 정보<br>2: 유해성·위험성<br>3: 구성성분의 명칭 및 함유량<br>4: 응급조치요령<br>5: 폭발·화재시 대처방법<br>6: 누출사고시 대처방법<br>7: 취급 및 저장방법<br>8: 노출방지 및 개인보호구<br>9: 물리화학적 특성<br>10: 안정성 및 반응성<br>11: 독성에 관한 정보<br>12: 환경에 미치는 영향<br>13: 폐기시 주의사항<br>14: 운송에 필요한 정보<br>15: 법적 규제현황<br>16: 그 밖의 참고사항 |

### `get_complete_msds`

화학물질의 전체 MSDS (16개 섹션)를 조회합니다. Get the complete MSDS (all 16 sections).

16회 호출을 동시에 보낸다. 일부 섹션이 실패하면 그 섹션에 error 를 넣고 나머지는 반환한다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `chem_id` | string | 예 |  | 화학물질ID 6자리 (search_chemicals 결과의 chem_id; 짧으면 0으로 채움) |

### `search_chemicals`

화학물질을 검색합니다. Search chemicals by name or identifier (CAS/UN/KE/EN No.).

Returns search_type_used, items[] (chem_id, chem_name_kor, cas_no, un_no, ke_no, en_no,
last_date), total_count, page_no, num_of_rows. 상세 조회에는 chem_id 를 쓴다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `search_term` | string | 예 |  | 검색어: 국문명, CAS No.(71-43-2), UN No.(UN1114), KE No.(KE-02150), EN No. |
| `search_type` | string (optional) |  |  | 검색 구분 (생략 시 자동 감지): KOREAN_NAME, CAS_NO, UN_NO, KE_NO, EN_NO |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대: 100) |

<!-- tools:end -->
