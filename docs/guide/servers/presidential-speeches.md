# 대통령기록관 연설문 (presidential-speeches)

역대 대통령 연설문 목록을 대통령·제목 키워드·연도·장소로 검색하고 원문 PDF 링크를 얻는다.

| | |
|---|---|
| 데이터셋 | [대통령기록관_대통령연설기록(연설문)](https://www.data.go.kr/data/15084167/fileData.do) (odcloud 파일데이터 API) |
| 활용신청 | **필요** — 페이지의 "오픈API" 탭에서 신청 |
| 환경변수 | `API_KEY` 또는 `PRESIDENTIAL_SPEECHES_API_KEY` |
| 패키지 | `data-go-mcp.presidential-speeches` (`src/presidential-speeches`) |

## 설정

```json
"presidential-speeches": {
  "command": "uvx",
  "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/presidential-speeches", "data-go-mcp.presidential-speeches"],
  "env": { "API_KEY": "<data.go.kr 인증키>" }
}
```

## 예시 프롬프트

- "노무현 대통령의 통일 관련 연설을 찾아줘"
- "2020년 연설문 목록"
- "가장 최근 연설 5건"
- "문재인 대통령의 마지막 연설들"

## 알아둘 것

- 검색은 서버측 필터(`cond[]`)로 전체 데이터를 대상으로 한다. `total_count` 는 조건에 맞는 전체 건수.
- 대통령 이름은 **정확히 일치**(예: `노무현`), 제목·장소는 부분 일치.
- 데이터셋은 2023-09 갱신본이며 **2022년 3월까지**의 연설이 들어 있다. 두 버전이 있는데 기본(2023본)은 `연설연도`, 옛 본(2022본, `use_2023_version=false`)은 `연설일자(YYYY-MM-DD)` 를 제공한다.
- 목록은 오래된 순이라 `list_speeches` 1페이지는 1948년이다. 최신은 `get_recent_speeches` 를 쓴다.
- 원본 데이터 품질: 일부 행의 연설연도에 `20220330` 같은 날짜가 들어 있다.

## 툴

<!-- tools:start -->

### `get_recent_speeches`

최근 대통령 연설문을 조회합니다. Get the most recent presidential speeches.

목록이 오래된 순이라 전체 건수를 먼저 구한 뒤 마지막 페이지를 읽어 최신순으로 돌려준다.
Returns count, president, data[] (최신 → 과거).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `president` | string (optional) |  |  | 대통령 이름 (정확히 일치, 예: 노무현) |
| `limit` | integer |  | `5` | 가져올 연설문 수 (기본값: 5) |

### `list_speeches`

대통령 연설문 목록을 조회합니다. List presidential speeches from the archives.

목록은 오래된 순(1948년부터)이다. 최신 연설은 get_recent_speeches 를 쓴다.
Returns total_count, page, per_page, data[] (id, president, title, source_url, location,
year 또는 date).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `page` | integer |  | `1` | 페이지 번호 (기본값: 1) |
| `per_page` | integer |  | `10` | 페이지당 결과 수 (기본값: 10) |
| `use_2023_version` | boolean |  | `True` | 2023 갱신본 사용 (연설연도 제공). False 면 2022 본 (연설일자 YYYY-MM-DD 제공) |

### `search_speeches`

대통령 연설문을 검색합니다. Search presidential speeches (server-side filters).

Returns total_count (조건에 맞는 전체 건수), page, per_page, data[].

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `president` | string (optional) |  |  | 대통령 이름 (정확히 일치, 예: 노무현) |
| `title` | string (optional) |  |  | 제목에 포함될 키워드 (부분 일치) |
| `year` | integer (optional) |  |  | 연설 연도 (예: 2020) |
| `location` | string (optional) |  |  | 연설 장소 (부분 일치, 예: 국내/국외) |
| `page` | integer |  | `1` | 페이지 번호 (기본값: 1) |
| `per_page` | integer |  | `10` | 페이지당 결과 수 (기본값: 10) |

<!-- tools:end -->
