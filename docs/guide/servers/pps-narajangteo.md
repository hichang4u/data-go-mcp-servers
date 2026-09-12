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
- "최근 일주일 공사 낙찰 정보를 알려줘"
- "9월 10일에 체결된 계약 현황"
- "입찰공고번호 R26BK01722116 의 상세를 보여줘 (공고일 9월 10일)"

## 알아둘 것

- 조회 범위 제한: 입찰공고·계약은 **1개월**, 낙찰은 **1주일**. 넘기면 API 가 오류(코드 07)를 돌려준다.
- 날짜를 생략하면 입찰공고·계약은 오늘, 낙찰은 최근 7일을 조회한다.
- 이 API 에는 공고번호 단건 조회가 없다. `get_bid_detail` 은 기간(기본 최근 30일)을 999건씩 최대 3페이지 훑어 찾으므로, 공고일을 알면 `start_date`/`end_date` 로 좁히는 편이 빠르고 확실하다.
- 항목은 API 원본 camelCase 필드(`bidNtceNo`, `bidNtceNm`, `ntceInsttNm`, `opengDate`, `presmptPrce` …)를 그대로 돌려준다.

## 툴

<!-- tools:start -->

### `get_bid_detail`

특정 입찰공고의 상세정보를 조회합니다. Get one bid announcement by its notice number.

이 API에는 공고번호 단건 조회가 없어, 공고일시 범위(기본: 최근 30일, 최대 1개월)를
999건씩 최대 3페이지까지 훑어 찾습니다. 공고일을 알면 start_date/end_date 로 좁히세요.

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

계약체결일자 기준. 검색 기간은 최대 1개월. 날짜를 지정하지 않으면 오늘을 검색합니다.

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

개찰일시 기준. 검색 기간은 최대 1주일. 날짜를 지정하지 않으면 최근 7일을 검색합니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `business_type` | string |  | `1` | 업무구분: 물품/외자/공사/용역 또는 코드 1/2/3/5 |
| `start_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |
| `end_date` | string (optional) |  |  | 날짜 (YYYY-MM-DD 또는 YYYYMMDD) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대: 999) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |

<!-- tools:end -->
