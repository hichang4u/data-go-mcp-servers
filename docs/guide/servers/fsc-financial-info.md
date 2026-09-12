# 금융위원회 기업 재무정보 (fsc-financial-info)

법인등록번호와 사업연도로 요약재무제표, 재무상태표, 손익계산서를 조회한다. 금액은 조·억·만 단위로 읽기 쉽게 포맷된 텍스트로 온다. 회사명·사업자등록번호로 법인등록번호를 찾는 `find_corp_number`, 기업 개요(대표자·상장시장·종업원 수·감사의견) `get_corp_outline`, KRX 일별 주식시세 `get_stock_price`/`search_stock_items` 를 함께 제공한다.

| | |
|---|---|
| 데이터셋 | [금융위원회_기업 재무정보](https://www.data.go.kr/data/15043459/openapi.do) (`GetFinaStatInfoService_V2`)<br>[금융위원회_기업기본정보](https://www.data.go.kr/data/15043184/openapi.do) (`GetCorpBasicInfoService_V2`, `find_corp_number`/`get_corp_outline` 용)<br>[금융위원회_주식시세정보](https://www.data.go.kr/data/15094808/openapi.do) (`GetStockSecuritiesInfoService_V2`, `get_stock_price`/`search_stock_items` 용) |
| 활용신청 | **필요, 세 API 모두** (자동승인) |
| 환경변수 | `API_KEY` 또는 `FSC_FINANCIAL_INFO_API_KEY` |
| 패키지 | `data-go-mcp.fsc-financial-info` (`src/fsc-financial-info`) |

## 설정

```json
"fsc-financial-info": {
  "command": "uvx",
  "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/fsc-financial-info", "data-go-mcp.fsc-financial-info"],
  "env": { "API_KEY": "<data.go.kr 인증키>" }
}
```

## 예시 프롬프트

- "삼성전자의 2023년 요약 재무제표를 조회해줘" (→ `find_corp_number` 로 법인등록번호를 찾은 뒤 조회)
- "사업자등록번호 124-81-00998 인 회사의 대표자와 종업원 수는?"
- "삼성전자 최근 열흘 주가와 시가총액" / "카카오 계열 상장사 목록과 시총"
- "법인등록번호 1301110006246의 2023년 요약 재무제표를 조회해줘" (삼성전자)
- "1301110006246 법인의 2023년 재무상태표에서 자산총계와 부채총계"
- "이 법인의 2023년 재무정보를 통합 조회해줘"

## 알아둘 것

- 재무제표의 키는 **법인등록번호(13자리)** 이지 사업자등록번호가 아니다. 모르면 `find_corp_number` 로 회사명(부분 일치) 또는 사업자등록번호(10자리)에서 찾는다.
- `find_corp_number` 의 `total_count` 는 API 의 레코드 수다. 한 법인이 유효기간별 스냅샷으로 여러 번 오기 때문에 법인 수(`items`)보다 크며, 툴은 법인별 최신 스냅샷만 남긴다. 흔한 이름("카카오")은 페이지가 넘칠 수 있으니 `(주)` 까지 붙여 좁힌다.
- `get_corp_outline` 의 종업원 수·평균 급여·감사의견은 공시 대상 법인에만 채워진다. 비상장 소규모 법인은 대부분 null.
- 주식시세는 **종목명(정확히 일치)·단축코드·ISIN** 으로만 조회된다. 법인등록번호로는 안 되므로 `get_corp_outline` 의 `enp_pban_cmpy_nm`(공시회사명, 예: "삼성전자")을 `itms_nm` 에 넣거나 `search_stock_items` 로 코드를 찾는다. 시세는 전 거래일까지 (하루 정도 지연).
- 사업연도는 4자리(`2023`). 연결/별도 재무제표가 각각 한 건씩 오는 경우가 많다.
- 재무상태표·손익계산서는 계정과목 단위로 페이징된다 (`num_of_rows` 최대 100).
- 조회 결과가 없으면 오류가 아니라 "조회된 … 없습니다" 텍스트가 온다.

## 툴

<!-- tools:start -->

### `find_corp_number`

법인명 또는 사업자등록번호로 법인등록번호(crno)를 찾습니다. 다른 재무정보 툴의 crno 입력에 씁니다. | Find the 13-digit corporate registration number (crno) by name or business number.

Returns one item per corporation (crno, corp_nm, bzno, market, representative, address).
total_count is the API's raw record count (one corporation can have several dated
snapshots), so it may exceed len(items); snapshots are collapsed within the page only,
so prefer a specific name or bzno over paging. Use get_corp_outline for the full profile.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `corp_name` | string (optional) |  |  | 법인명 (부분 일치, 예: '삼성전자(주)') \| Corporate name (partial match) |
| `bzno` | string (optional) |  |  | 사업자등록번호 (10자리, 하이픈 허용) \| Business registration number |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) \| Page number (default: 1) |
| `num_of_rows` | integer |  | `100` | 한 페이지 조회 레코드 수 (기본값: 100, 최대: 100) \| Records per page |

### `get_balance_sheet`

기업의 재무상태표(대차대조표)를 조회합니다. 자산, 부채, 자본의 세부 계정과목별 금액을 확인할 수 있습니다. | Get balance sheet with detailed account items for assets, liabilities, and equity.

Args:
    crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
    biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)
    page_no: 페이지 번호 (기본값: 1) | Page number (default: 1)
    num_of_rows: 한 페이지 결과 수 (기본값: 10, 최대: 100) | Number of rows per page (default: 10, max: 100)

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `crno` | string (optional) |  |  | 법인등록번호 (13자리 숫자, 하이픈 제외; 모르면 find_corp_number 로 조회) \| Corporate registration number (13 digits) |
| `biz_year` | string (optional) |  |  | 사업연도 (예: 2023) \| Business year (e.g., 2023) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) \| Page number (default: 1) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대: 100) \| Number of rows per page (default: 10, max: 100) |

### `get_corp_outline`

법인등록번호로 기업 개요를 조회합니다: 대표자, 주소, 상장시장, 설립일, 종업원 수, 평균 급여, 감사인·감사의견 등. | Get the corporate profile (representative, address, market, employees, average salary, auditor) by crno.

Returns the latest snapshot (snapshot_dt). Empty or undisclosed fields (including 0
employees / 0 salary) are null.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `crno` | string | 예 |  | 법인등록번호 (13자리 숫자, 하이픈 제외; 모르면 find_corp_number 로 조회) \| Corporate registration number (13 digits) |

### `get_income_statement`

기업의 손익계산서를 조회합니다. 매출, 비용, 이익 등의 세부 계정과목별 금액을 확인할 수 있습니다. | Get income statement with detailed account items for revenue, expenses, and profit.

Args:
    crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
    biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)
    page_no: 페이지 번호 (기본값: 1) | Page number (default: 1)
    num_of_rows: 한 페이지 결과 수 (기본값: 10, 최대: 100) | Number of rows per page (default: 10, max: 100)

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `crno` | string (optional) |  |  | 법인등록번호 (13자리 숫자, 하이픈 제외; 모르면 find_corp_number 로 조회) \| Corporate registration number (13 digits) |
| `biz_year` | string (optional) |  |  | 사업연도 (예: 2023) \| Business year (e.g., 2023) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) \| Page number (default: 1) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대: 100) \| Number of rows per page (default: 10, max: 100) |

### `get_stock_price`

KRX 상장 주식의 일별 시세를 조회합니다: 종가, 등락, 시가·고가·저가, 거래량, 시가총액. 최신 거래일부터 내려옵니다. | Get daily KRX stock prices (close, change, OHLC, volume, market cap), newest first.

Give one of itms_nm / srtn_cd / isin_cd. Data lags the market by about one trading day.
To find the exact 종목명 or ticker, use search_stock_items.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `itms_nm` | string (optional) |  |  | 종목명 (정확히 일치, 예: '삼성전자'; get_corp_outline 의 enp_pban_cmpy_nm) \| Exact stock name |
| `srtn_cd` | string (optional) |  |  | 단축코드 (6자리, 예: 005930) \| 6-digit ticker |
| `isin_cd` | string (optional) |  |  | ISIN 코드 (예: KR7005930003) \| ISIN code |
| `bas_dt` | string (optional) |  |  | 기준일자 (YYYYMMDD) \| Trading date — 하루만 |
| `begin_bas_dt` | string (optional) |  |  | 기준일자 (YYYYMMDD) \| Trading date 시작 (이상) |
| `end_bas_dt` | string (optional) |  |  | 기준일자 (YYYYMMDD) \| Trading date 끝 (이하) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) \| Page number (default: 1) |
| `num_of_rows` | integer |  | `10` | 거래일 수 (기본값: 10, 최대: 100) \| Trading days per page |

### `get_summary_financial_statement`

기업의 요약 재무제표를 조회합니다. 매출액, 영업이익, 당기순이익, 자산, 부채 등 주요 재무지표를 확인할 수 있습니다. | Get summary financial statements including revenue, operating profit, net income, assets, and liabilities.

Args:
    crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
    biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)
    page_no: 페이지 번호 (기본값: 1) | Page number (default: 1)
    num_of_rows: 한 페이지 결과 수 (기본값: 10, 최대: 100) | Number of rows per page (default: 10, max: 100)

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `crno` | string (optional) |  |  | 법인등록번호 (13자리 숫자, 하이픈 제외; 모르면 find_corp_number 로 조회) \| Corporate registration number (13 digits) |
| `biz_year` | string (optional) |  |  | 사업연도 (예: 2023) \| Business year (e.g., 2023) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) \| Page number (default: 1) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대: 100) \| Number of rows per page (default: 10, max: 100) |

### `search_company_financial_info`

법인등록번호로 기업의 전체 재무정보를 통합 조회합니다. 요약 재무제표, 재무상태표, 손익계산서를 한번에 가져옵니다. | Search comprehensive financial information by corporate registration number, including summary, balance sheet, and income statement.

Args:
    crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
    biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `crno` | string | 예 |  | 법인등록번호 (13자리 숫자, 하이픈 제외; 모르면 find_corp_number 로 조회) \| Corporate registration number (13 digits) |
| `biz_year` | string | 예 |  | 사업연도 (예: 2023) \| Business year (e.g., 2023) |

### `search_stock_items`

종목명 일부로 상장 종목을 찾습니다. 최신 거래일 기준 종목당 한 건(코드, 시장, 종가, 시가총액). | Search listed stocks by partial name; one row per item as of the latest trading day.

Use the returned itms_nm or srtn_cd with get_stock_price for history.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `name` | string | 예 |  | 종목명 일부 (예: '삼성', '카카오') \| Partial stock name |
| `num_of_rows` | integer |  | `50` | 최대 종목 수 (기본값: 50, 최대: 100) \| Max items |

<!-- tools:end -->
