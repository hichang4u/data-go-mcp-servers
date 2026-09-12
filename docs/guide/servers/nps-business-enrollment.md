# 국민연금공단 사업장 가입내역 (nps-business-enrollment)

국민연금에 가입된 사업장을 이름·사업자번호·주소코드로 찾고, 가입자 수와 당월 고지금액, 월별 취득·상실 인원을 조회한다.

| | |
|---|---|
| 데이터셋 | [국민연금공단_국민연금 가입 사업장 내역](https://www.data.go.kr/data/3046071/openapi.do) (`NpsBplcInfoInqireServiceV2`) |
| 활용신청 | **필요** — 포털에서 신청 후 승인 즉시 반영 (자동승인) |
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
- "서울시 강남구(법정동코드 11680)에 있는 사업장 목록을 보여줘"
- "seq 7101020 사업장의 가입자 수와 추정 평균 월급을 알려줘"

## 알아둘 것

- `search_business` 결과의 `seq` 가 상세·기간별 조회의 키다.
- `estimated_avg_monthly_salary` 는 `당월고지금액 ÷ 가입자수 ÷ 0.09(보험료율)` 로 계산한 **추정값**이다. 상한액·감면 등을 반영하지 않는다.
- 사업자등록번호는 앞 6자리만 검색된다. 응답의 번호도 뒷자리가 마스킹돼 있다.

## 툴

<!-- tools:start -->

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
Returns items, page_no, num_of_rows, total_count, message.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `ldong_addr_mgpl_dg_cd` | string (optional) |  |  | 법정동주소 광역시도 코드 (2자리) |
| `ldong_addr_mgpl_sggu_cd` | string (optional) |  |  | 법정동주소 시군구 코드 (5자리) |
| `ldong_addr_mgpl_sggu_emd_cd` | string (optional) |  |  | 법정동주소 읍면동 코드 (8자리) |
| `wkpl_nm` | string (optional) |  |  | 사업장명 (부분 일치) |
| `bzowr_rgst_no` | string (optional) |  |  | 사업자등록번호 (앞 6자리) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |
| `num_of_rows` | integer |  | `100` | 한 페이지 결과 수 (기본값: 100, 최대: 100) |

<!-- tools:end -->
