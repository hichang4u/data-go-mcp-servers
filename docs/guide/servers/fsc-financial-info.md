# 금융위원회 기업 재무정보 (fsc-financial-info)

법인등록번호와 사업연도로 요약재무제표, 재무상태표, 손익계산서를 조회한다. 금액은 조·억·만 단위로 읽기 쉽게 포맷된 텍스트로 온다.

| | |
|---|---|
| 데이터셋 | [금융위원회_기업 재무정보](https://www.data.go.kr/data/15043459/openapi.do) (`GetFinaStatInfoService_V2`) |
| 활용신청 | **필요** (자동승인) |
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

- "법인등록번호 1301110006246의 2023년 요약 재무제표를 조회해줘" (삼성전자)
- "1301110006246 법인의 2023년 재무상태표에서 자산총계와 부채총계"
- "이 법인의 2023년 재무정보를 통합 조회해줘"

## 알아둘 것

- 키는 **법인등록번호(13자리)** 이지 사업자등록번호가 아니다. 회사명 검색은 제공되지 않는다.
- 사업연도는 4자리(`2023`). 연결/별도 재무제표가 각각 한 건씩 오는 경우가 많다.
- 재무상태표·손익계산서는 계정과목 단위로 페이징된다 (`num_of_rows` 최대 100).
- 조회 결과가 없으면 오류가 아니라 "조회된 … 없습니다" 텍스트가 온다.

## 툴

<!-- tools:start -->

### `get_balance_sheet`

기업의 재무상태표(대차대조표)를 조회합니다. 자산, 부채, 자본의 세부 계정과목별 금액을 확인할 수 있습니다. | Get balance sheet with detailed account items for assets, liabilities, and equity.

Args:
    crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
    biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)
    page_no: 페이지 번호 (기본값: 1) | Page number (default: 1)
    num_of_rows: 한 페이지 결과 수 (기본값: 10, 최대: 100) | Number of rows per page (default: 10, max: 100)

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `crno` | string (optional) |  |  | 법인등록번호 (13자리 숫자, 하이픈 제외) \| Corporate registration number (13 digits) |
| `biz_year` | string (optional) |  |  | 사업연도 (예: 2023) \| Business year (e.g., 2023) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) \| Page number (default: 1) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대: 100) \| Number of rows per page (default: 10, max: 100) |

### `get_income_statement`

기업의 손익계산서를 조회합니다. 매출, 비용, 이익 등의 세부 계정과목별 금액을 확인할 수 있습니다. | Get income statement with detailed account items for revenue, expenses, and profit.

Args:
    crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
    biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)
    page_no: 페이지 번호 (기본값: 1) | Page number (default: 1)
    num_of_rows: 한 페이지 결과 수 (기본값: 10, 최대: 100) | Number of rows per page (default: 10, max: 100)

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `crno` | string (optional) |  |  | 법인등록번호 (13자리 숫자, 하이픈 제외) \| Corporate registration number (13 digits) |
| `biz_year` | string (optional) |  |  | 사업연도 (예: 2023) \| Business year (e.g., 2023) |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) \| Page number (default: 1) |
| `num_of_rows` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대: 100) \| Number of rows per page (default: 10, max: 100) |

### `get_summary_financial_statement`

기업의 요약 재무제표를 조회합니다. 매출액, 영업이익, 당기순이익, 자산, 부채 등 주요 재무지표를 확인할 수 있습니다. | Get summary financial statements including revenue, operating profit, net income, assets, and liabilities.

Args:
    crno: 법인등록번호 (13자리 숫자, 하이픈 제외) | Corporate registration number (13 digits)
    biz_year: 사업연도 (예: 2023) | Business year (e.g., 2023)
    page_no: 페이지 번호 (기본값: 1) | Page number (default: 1)
    num_of_rows: 한 페이지 결과 수 (기본값: 10, 최대: 100) | Number of rows per page (default: 10, max: 100)

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `crno` | string (optional) |  |  | 법인등록번호 (13자리 숫자, 하이픈 제외) \| Corporate registration number (13 digits) |
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
| `crno` | string | 예 |  | 법인등록번호 (13자리 숫자, 하이픈 제외) \| Corporate registration number (13 digits) |
| `biz_year` | string | 예 |  | 사업연도 (예: 2023) \| Business year (e.g., 2023) |

<!-- tools:end -->
