# 한국은행 경제통계시스템 ECOS (bok-ecos)

기준금리·환율·물가·가계신용 같은 거시 경제통계를 통계표 코드로 조회한다. 기업 재무(fsc)나 공시(dart-disclosure)를 볼 때 그 시기의 금리·환율을 함께 놓고 보는 용도.

## 데이터셋

| 서비스 | 내용 | 쓰는 툴 |
|---|---|---|
| KeyStatisticList | 100대 통계지표 최신값 | `get_key_statistics` |
| StatisticTableList | 통계표 목록 (약 844건) | `find_statistic_table` |
| StatisticItemList | 통계표의 세부항목·조회 가능 기간 | `get_statistic_items` |
| StatisticSearch | 통계 시계열 | `get_statistic_data` |
| StatisticWord | 통계용어사전 | `search_term` |

## 인증키

data.go.kr 이 아니라 [ecos.bok.or.kr](https://ecos.bok.or.kr) 에서 따로 발급한다 — [api-keys.md](../api-keys.md) 5절. 환경변수는 `BOK_ECOS_API_KEY` 이며 공통 `API_KEY` 는 쓰이지 않는다.

키 없이 바로 시험해 보려면 `BOK_ECOS_API_KEY=sample` 을 쓸 수 있다. 단 **한 번에 10건까지만** 오고 넘기면 `ERROR-301` 이 난다.

## 예시 프롬프트

- "한국은행 기준금리 최근 1년 추이를 보여줘"
- "지금 원/달러 환율이 얼마야"
- "소비자물가지수 통계표 코드를 찾아줘"
- "가계신용 2024년 분기별 잔액"
- "경상수지가 무슨 뜻이야"

## 알아둘 것

- 툴은 **통계표 코드(stat_code)** 로 움직인다. 코드를 모르면 `find_statistic_table` → `get_statistic_items` → `get_statistic_data` 순으로 좁힌다. 100대 지표만 필요하면 `get_key_statistics` 로 코드 없이 바로 본다.
- 시점 형식은 **주기를 따른다**: 년 `2024`, 분기 `2024Q1`, 월 `202401`, 일 `20240115` (반기 `2024S1`, 반월 `202401S1`). 주기와 형식이 어긋나면 툴이 `입력값 오류` 로 막는다.
- 같은 항목이 주기마다 한 줄씩 오고 조회 가능 기간도 주기별로 다르다. `get_statistic_items` 의 `start_time`/`end_time` 을 그대로 쓰면 어긋나지 않는다.
- `get_statistic_data` 에서 항목 코드를 생략하면 그 통계표의 **모든 항목**이 온다. 건수가 빠르게 늘어나니 항목을 알면 지정한다 (최대 4개).
- 해당 기간에 자료가 없으면 오류가 아니라 빈 결과다 (ECOS `INFO-200`).
- 통계표 이름 검색 API 가 없어 `find_statistic_table` 은 전체 목록을 받아 거른다. 목록은 서버 프로세스 안에 한 번만 받아 둔다.

## 툴

<!-- tools:start -->

### `find_statistic_table`

통계표 코드를 이름으로 찾습니다. Find ECOS statistic table codes by name.

다른 툴은 모두 통계표 코드(stat_code)를 요구하므로 여기서 먼저 찾습니다. ECOS 에는 이름 검색
API 가 없어 전체 목록(약 844건)을 받아 거르며, 목록은 프로세스 안에 한 번만 받아 둡니다.
조회할 수 없는 분류 노드(SRCH_YN=N)는 제외합니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `keyword` | string | 예 |  | 통계표 이름에 포함된 말 (예: 기준금리, 환율, 소비자물가) |
| `cycle` | string (optional) |  |  | 주기로 좁히기: A=년 (YYYY), S=반기 (YYYYS1, S2), Q=분기 (YYYYQ1~Q4), M=월 (YYYYMM), SM=반월 (YYYYMMS1, S2), D=일 (YYYYMMDD) |
| `limit` | integer |  | `20` | 최대 결과 수 (기본값: 20) |

### `get_key_statistics`

100대 통계지표의 최신값을 봅니다. Get the latest values of 100 key indicators.

환율·기준금리·물가 같은 대표 지표를 코드 없이 바로 봅니다. 각 항목의 time 은 지표마다 기준
시점이 달라(일/월) 그대로 돌려줍니다. 시계열이 필요하면 get_statistic_data 를 쓰세요.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `class_name` | string (optional) |  |  | 지표 분류로 좁히기 (예: 환율, 금리, 국민계정, 물가). 부분 일치 |
| `num_of_rows` | integer |  | `100` | 한 페이지 결과 수 (기본값: 100. sample 키는 10을 넘기면 오류) |

### `get_statistic_data`

통계 시계열을 조회합니다. Get an ECOS statistic time series.

시점(time)과 값(value)을 시계열로 돌려줍니다. 항목 코드를 생략하면 통계표의 모든 항목이 오므로
건수가 빠르게 늘어납니다 — 항목을 아는 경우 지정하세요 (최대 4개). 조회 가능 기간은
get_statistic_items 가 알려줍니다. 해당 기간에 자료가 없으면 빈 결과입니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `stat_code` | string | 예 |  | 통계표 코드 (예: 722Y001) |
| `cycle` | string | 예 |  | 주기: A=년 (YYYY), S=반기 (YYYYS1, S2), Q=분기 (YYYYQ1~Q4), M=월 (YYYYMM), SM=반월 (YYYYMMS1, S2), D=일 (YYYYMMDD) |
| `start_time` | string | 예 |  | 시작 시점. 주기 형식에 맞춘다 (예: 202401) |
| `end_time` | string | 예 |  | 종료 시점. 주기 형식에 맞춘다 (예: 202412) |
| `item_code1` | string (optional) |  |  | 항목 코드 1. 생략하면 통계표의 모든 항목 |
| `item_code2` | string (optional) |  |  | 항목 코드 2 |
| `item_code3` | string (optional) |  |  | 항목 코드 3 |
| `item_code4` | string (optional) |  |  | 항목 코드 4 |
| `num_of_rows` | integer |  | `100` | 한 페이지 결과 수 (기본값: 100. sample 키는 10을 넘기면 오류) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |

### `get_statistic_items`

통계표의 세부항목과 조회 가능 기간을 봅니다. List items and searchable periods.

항목 코드(item_code)와 주기(cycle)별 start_time/end_time 을 돌려줍니다. 같은 항목이 주기마다
한 줄씩 오고 시점 형식도 주기를 따르므로(월 199901, 분기 2002Q4), 여기 값을 그대로
get_statistic_data 에 넘기면 됩니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `stat_code` | string | 예 |  | 통계표 코드 (예: 722Y001) |
| `num_of_rows` | integer |  | `100` | 한 페이지 결과 수 (기본값: 100. sample 키는 10을 넘기면 오류) |

### `search_term`

통계 용어의 뜻을 찾습니다. Look up an economic statistics term.

한국은행 통계용어사전의 설명을 돌려줍니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `word` | string | 예 |  | 찾을 통계 용어 (예: 기준금리, 경상수지) |
| `num_of_rows` | integer |  | `100` | 한 페이지 결과 수 (기본값: 100. sample 키는 10을 넘기면 오류) |

<!-- tools:end -->
