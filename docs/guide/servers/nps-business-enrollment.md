# 국민연금공단 사업장 가입내역 (nps-business-enrollment)

국민연금에 가입된 사업장을 이름·사업자번호·지역으로 찾고, 가입자 수와 당월 고지금액, 월별 취득·상실 인원을 조회한다. 지역명을 법정동코드로 바꿔 주는 `find_region_code` 를 함께 제공한다.

| | |
|---|---|
| 데이터셋 | [국민연금공단_국민연금 가입 사업장 내역](https://www.data.go.kr/data/3046071/openapi.do) (`NpsBplcInfoInqireServiceV2`)<br>[행정안전부_행정표준코드_법정동코드](https://www.data.go.kr/data/15077871/openapi.do) (`StanReginCd`, `find_region_code` 용) |
| 활용신청 | **필요, 두 API 모두** — 포털에서 신청 후 승인 즉시 반영 (자동승인) |
| 환경변수 | `API_KEY` 또는 `NPS_BUSINESS_ENROLLMENT_API_KEY` |
| 패키지 | `data-go-mcp.nps-business-enrollment` (`src/nps-business-enrollment`) |

## 설정

```json
"nps-business-enrollment": {
  "command": "uvx",
  "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nps-business-enrollment", "data-go-mcp.nps-business-enrollment"],
  "env": { "API_KEY": "<data.go.kr 인증키>" }
}
```

## 예시 프롬프트

- "삼성전자 사업장 정보를 찾아줘"
- "사업자등록번호 124815로 시작하는 사업장을 조회해줘"
- "강남구 역삼동에 있는 삼성 관련 사업장을 찾아줘" (→ `find_region_code` 로 코드를 얻어 `search_business`)
- "seq 7101020 사업장의 가입자 수와 추정 평균 월급을 알려줘"

## 알아둘 것

- `search_business` 결과의 `seq` 가 상세·기간별 조회의 키다.
- `estimated_avg_monthly_salary` 는 `당월고지금액 ÷ 가입자수 ÷ 0.09(보험료율)` 로 계산한 **추정값**이다. 상한액·감면 등을 반영하지 않는다.
- 사업자등록번호는 앞 6자리만 검색된다. 응답의 번호도 뒷자리가 마스킹돼 있다.
- 지역 필터는 시도(2자리)·시군구(3자리)·읍면동(3자리) 코드다. 시군구는 시도와, 읍면동은 시도·시군구와 함께 줘야 적용된다. `find_region_code` 결과의 `nps_params` 를 그대로 넘기면 된다. 리(里) 단위 필터는 없다.
- `find_region_code` 는 부분 일치라 "강남" 은 다른 지역의 강남동도 포함한다. 시도명까지 붙이면 좁혀진다.

## 툴

<!-- tools:start -->

### `find_region_code`

지역명으로 법정동코드를 찾습니다.

Look up 법정동코드 (행정안전부 행정표준코드) by region name. Each item has level
(시도/시군구/읍면동/리) and nps_params — the exact ldong_addr_mgpl_* arguments for
search_business. Within a page, higher-level regions are listed first; when
total_count exceeds the page, narrow the name or use page_no.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `name` | string | 예 |  | 지역명 (부분 일치, 예: '강남구', '서울특별시 강남구 역삼동', '가평읍') |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |
| `num_of_rows` | integer |  | `100` | 한 페이지 결과 수 (기본값: 100) |

### `get_business_detail`

사업장 상세정보를 조회합니다.

Get detailed information about a specific business enrollment: name, registration
number, address, industry, registration/withdrawal dates, subscribers, monthly billing
amount, and an estimated average monthly salary (추정값).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `seq` | integer | 예 |  | 사업장 식별번호 (search_business 결과의 seq) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10) |

### `get_period_status`

사업장의 기간별 현황 정보를 조회합니다.

Get period-based status: nw_acqzr_cnt (new acquisitions), lss_jnngp_cnt (losses),
plus estimated_avg_monthly_salary (추정값) taken from the business detail.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `seq` | integer | 예 |  | 사업장 식별번호 (search_business 결과의 seq) |
| `data_crt_ym` | string (optional) |  |  | 조회할 년월 (YYYYMM) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10) |

### `search_business`

사업장 정보를 조회합니다.

Search for business enrollment information in the National Pension Service.
Region filters take the codes returned by find_region_code (nps_params).
Returns items, page_no, num_of_rows, total_count, message.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `ldong_addr_mgpl_dg_cd` | string (optional) |  |  | 법정동주소 광역시도 코드 (2자리, find_region_code 의 sido_cd) |
| `ldong_addr_mgpl_sggu_cd` | string (optional) |  |  | 법정동주소 시군구 코드 (3자리, find_region_code 의 sgg_cd). 광역시도 코드와 함께 줘야 적용된다 |
| `ldong_addr_mgpl_sggu_emd_cd` | string (optional) |  |  | 법정동주소 읍면동 코드 (3자리, find_region_code 의 umd_cd). 광역시도·시군구 코드와 함께 줘야 적용된다 |
| `wkpl_nm` | string (optional) |  |  | 사업장명 (부분 일치) |
| `bzowr_rgst_no` | string (optional) |  |  | 사업자등록번호 (앞 6자리) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |
| `num_of_rows` | integer |  | `100` | 한 페이지 결과 수 (기본값: 100, 최대: 100) |

<!-- tools:end -->
