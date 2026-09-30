# 조달청 나라장터 입찰·낙찰·계약 (pps-narajangteo)

나라장터 공공데이터개방표준서비스로 입찰공고, 낙찰, 계약 정보를 기간 기준으로 조회한다.

| | |
|---|---|
| 데이터셋 | 조달청_나라장터 공공데이터개방표준서비스 (`PubDataOpnStdService`) |
| 활용신청 | 필요 (자동승인) |
| 환경변수 | `API_KEY` 또는 `PPS_NARAJANGTEO_API_KEY` |
| 패키지 | `data-go-mcp.pps-narajangteo` (`src/pps-narajangteo`) |

## 설정

```json
"pps-narajangteo": {
  "command": "uvx",
  "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/pps-narajangteo", "data-go-mcp.pps-narajangteo"],
  "env": { "API_KEY": "<data.go.kr 인증키>" }
}
```

## 예시 프롬프트

- "오늘 공고된 입찰정보를 보여줘"
- "2026년 9월 1일부터 12일까지 입찰공고 20건"
- "지난 금요일 공사 낙찰 정보를 알려줘"
- "9월 10일에 체결된 계약 현황"
- "입찰공고번호 R26BK01722116 의 상세를 보여줘 (공고일 9월 10일)"
- "사업자번호 214-87-12538 이 지난달 낙찰받은 용역이 있어?"

## 알아둘 것

- 조회 범위 제한 (2026-09-20 실호출로 확인, 문서와 다르다): 입찰공고 **1개월**, 계약 **7일**(8일부터 코드 07), 낙찰 **하루**(이틀부터 07). 넘기면 툴이 `입력값 오류` 로 먼저 막고, API 가 돌려주는 07 도 오류로 전달된다.
- 날짜를 생략하면 입찰공고·계약은 오늘, 낙찰은 **직전 평일**을 조회한다 (당일 개찰은 진행 중이라 불완전). 하루 낙찰이 물품 2만·용역 6천·공사 9만 건 규모라 `business_type` 과 `num_of_rows`/`page_no` 로 나눠 본다.
- 이 API 에는 공고번호 단건 조회가 없다. `get_bid_detail` 은 기간(기본 최근 7일)을 999건씩 최대 12페이지(약 1만 2천 건) 훑는데, 공고가 하루 1,100건 이상이고 날짜순으로 오지 않아 열흘 남짓이 한계다. 공고일을 알면 `start_date` 로 그날만 지정하는 것이 가장 빠르다 (하루 = 2페이지, 3~4초).
- 항목은 API 원본 camelCase 필드(`bidNtceNo`, `bidNtceNm`, `ntceInsttNm`, `opengDate`, `presmptPrce` …)를 그대로 돌려준다.

### 낙찰업체로 찾기

`find_bid_winners` 는 특정 업체의 낙찰 이력을 찾는다. 다른 툴과 달리 **낙찰정보서비스**(`as/ScsbidInfoService`)를 쓴다 — 낙찰업체 사업자번호·상호가 이 서비스 응답에만 있기 때문이다.

- 나라장터 API 는 **업체로 검색할 수 없다.** 사업자번호를 요청 파라미터로 줘도 무시되고 전체가 온다. 그래서 기간 안의 낙찰 건을 999건씩 전부 받아 클라이언트에서 거른다.
- 그래서 **기간이 길수록 느리다**: 용역 1개월이 약 15~35초(4~8페이지), 3개월이 약 60초. 기본은 최근 1개월, **최대 3개월**이다. API 한도가 한 요청에 1개월이라 그보다 길면 달 단위로 나눠 호출한다.
- 결과의 `complete` 가 `false` 면 기간을 다 훑지 못한 것이다 — 이때의 "0건"은 "없음"이 아니다.
- 업무구분 하나만 훑는다. 용역·물품·공사·외자를 모두 보려면 각각 호출해야 한다 (3개월 × 3종은 3분이 넘는다).
- 개찰일시 기준이다. 사업자번호는 정확 일치, 업체명은 부분 일치로 거른다.
- 오래된 달일수록 건수가 많다 (정정·추가 등록이 쌓인다) — 2026년 7월 용역은 7,498건으로 9월(3,272건)의 두 배다.

## 툴

<!-- tools:start -->

### `find_bid_winners`

특정 업체의 나라장터 낙찰 이력을 찾습니다. Find a company's winning bids.

나라장터 API 는 낙찰업체로 **검색할 수 없어서**, 기간 안의 낙찰 건을 전부 받아 걸러냅니다.
그래서 기간이 길수록 느립니다 — 용역 1개월이 약 15~35초, 3개월이 약 60초입니다. 기본은 최근
1개월이고 **최대 3개월**까지입니다 (API 한도가 한 요청에 1개월이라 내부에서 달 단위로 나눠
호출합니다). 업무구분을 하나만 지정하므로 다른 구분의 낙찰은 잡히지 않습니다
(용역/물품/공사/외자를 각각 호출하세요). 개찰일시 기준입니다.

complete=false 면 기간을 다 훑지 못한 것이니 "0건"을 없다는 뜻으로 읽으면 안 됩니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `business_number` | string (optional) |  |  | 낙찰업체 사업자등록번호 10자리 (하이픈 허용) |
| `company_name` | string (optional) |  |  | 낙찰업체 상호 (부분 일치). 사업자번호가 더 정확하다 |
| `business_type` | string |  | `용역` | 업무구분: 용역, 물품, 공사, 외자 |
| `start_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |
| `end_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |

### `get_bid_detail`

특정 입찰공고의 상세정보를 조회합니다. Get one bid announcement by its notice number.

이 API에는 공고번호 단건 조회가 없어 공고일시 범위(기본: 최근 7일)를 999건씩 최대 12페이지
(약 1만 2천 건, 열흘치) 훑어 찾습니다. 공고는 하루 1,100건 이상이고 날짜순으로 오지 않으므로,
공고일을 알면 start_date(=end_date) 로 그날만 지정하세요 — 가장 빠르고 확실합니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `bid_notice_no` | string | 예 |  | 입찰공고번호 (예: R25BK00933743) |
| `start_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |
| `end_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |

### `search_bid_announcements`

나라장터 입찰공고정보를 검색합니다. Search bid announcements in the G2B marketplace.

검색 기간은 최대 1개월. 날짜를 지정하지 않으면 오늘 하루를 검색합니다.
Returns items (raw camelCase fields such as bidNtceNo, bidNtceNm, ntceInsttNm, opengDate),
total_count, page_no, num_of_rows, search_period.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `start_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |
| `end_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대: 999) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |

### `search_contracts`

나라장터 계약정보를 검색합니다. Search contracts in the G2B marketplace.

계약체결일자 기준. 검색 기간은 **최대 7일** (API 제한). 날짜를 지정하지 않으면 오늘을 검색합니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `start_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |
| `end_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |
| `institution_type` | string (optional) |  |  | 기관구분코드 (1: 계약기관, 2: 수요기관) |
| `institution_code` | string (optional) |  |  | 기관코드 (7자리) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대: 999) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |

### `search_successful_bids`

나라장터 낙찰정보를 검색합니다. Search successful bids in the G2B marketplace.

개찰일시 기준으로 **하루**만 조회할 수 있습니다 (API 제한). 날짜를 지정하지 않으면 직전 평일을
검색합니다 (당일 개찰은 진행 중이라 불완전). 하루에 물품 2만·공사 9만 건 규모이니 num_of_rows 와
page_no 로 나눠 보세요.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `business_type` | string |  | `1` | 업무구분: 물품/외자/공사/용역 또는 코드 1/2/3/5 |
| `start_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |
| `end_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대: 999) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |

<!-- tools:end -->
