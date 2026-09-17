# 금융감독원 전자공시 DART (dart-disclosure)

회사명으로 DART 고유번호를 찾고, 기업 개황·공시 목록·정기보고서 재무제표(주요계정, 전체 XBRL 계정)·공시 원문 텍스트를 조회한다. 상장사와 외부감사 대상 법인의 공시가 대상이다.

| | |
|---|---|
| 데이터셋 | 금융감독원 OpenDART — `opendart.fss.or.kr/api` (data.go.kr 계열이 **아님**) |
| 활용신청 | [opendart.fss.or.kr](https://opendart.fss.or.kr) 회원가입 → 인증키 신청/관리 → 인증키 신청 (즉시 발급, 일 20,000건) |
| 환경변수 | `DART_DISCLOSURE_API_KEY` — data.go.kr 키(`API_KEY`)는 쓰이지 않는다 |
| 패키지 | `data-go-mcp.dart-disclosure` (`src/dart-disclosure`) |

## 설정

```json
"dart-disclosure": {
  "command": "uvx",
  "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/dart-disclosure", "data-go-mcp.dart-disclosure"],
  "env": { "DART_DISCLOSURE_API_KEY": "<OpenDART 인증키>" }
}
```

## 예시 프롬프트

- "카카오의 DART 고유번호 찾아줘"
- "삼성전자 2024년 사업보고서의 연결 손익계산서"
- "삼성전자가 올해 낸 정기공시 목록"
- "접수번호 20250311001085 의 사업보고서 원문에서 '주요 제품' 부분 읽어줘"
- "LG에너지솔루션 2025년 1분기 영업이익과 전년 동기 비교"

## 알아둘 것

- 모든 조회의 키는 **고유번호(`corp_code`, 8자리)** 다. 종목코드·법인등록번호와 다르다. `find_corp_code` 로 회사명이나 6자리 종목코드에서 찾는다.
- `find_corp_code` 는 API 를 부르지 않고 패키지에 동봉한 전체 기업 목록 스냅샷(약 12만 개사)을 검색한다. 결과의 `snapshot_date` 이후에 등록된 회사는 없을 수 있다. 같은 이름의 비상장 법인이 많으므로(`신한` 11개) `listed_only` 를 켜거나 `get_company` 로 확인한다.
- `get_company` 의 `jurir_no`(법인등록번호 13자리)는 fsc-financial-info 툴의 `crno` 로 그대로 쓸 수 있다.
- `list_disclosures` 는 `corp_code` 없이 부르면 검색 기간이 **3개월 이내**여야 한다 (API 제한). `bgn_de` 를 생략하면 회사 지정 시 1년, 아니면 30일 전부터(`end_de` 를 주면 그 날 기준) 검색한다 — API 기본값(당일만)을 그대로 두면 거의 항상 0건이라 서버가 채운다.
- 재무제표 툴(`get_key_accounts`, `get_financial_statements`)은 **2015년 이후 상장사** 정기보고서만 제공한다. 금액은 원 단위 정수. `get_financial_statements` 는 사업보고서 한 건이 200행 안팎이라 `sj_div` 로 한 표만 받는 것이 좋다. 분기 보고서의 `thstrm_add_amount` 가 누적 금액.
- `get_disclosure_document` 는 원문 HTML 을 텍스트로 바꿔 준다. 사업보고서는 60만 자 이상이라 기본 20,000자씩 `offset` 으로 나눠 읽는다 (최근 4건은 프로세스 안에 캐시되어 페이지마다 다시 받지 않는다). 표는 셀이 공백으로 이어진 한 줄이 된다. 첨부(감사보고서 등)는 `attachment_files` 에 이름만.
- 오류 메시지는 `OpenDART 오류 [코드]` 로 온다. `010`/`011` 키 문제, `020` 일일 한도 초과, `100` 파라미터 오류(기간 3개월 초과 등), `013` 은 결과 없음(오류가 아니라 빈 결과).

## 툴

<!-- tools:start -->

### `find_corp_code`

회사명 또는 종목코드로 DART 고유번호(corp_code)를 찾습니다. 다른 툴의 corp_code 입력에 씁니다. | Find the 8-digit DART corp_code by company name or stock code.

Returns items (corp_code, corp_name, stock_code, corp_eng_name), total_count, snapshot_date.
Exact name match ranks first, then prefix, then partial; listed companies before unlisted.
Searches a bundled snapshot of all ~120k DART-registered companies (no API call);
snapshot_date is when it was taken, so companies registered after that are missing.
Same-name companies are common (e.g. 11 "신한") — check stock_code or use get_company to confirm.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `query` | string | 예 |  | 회사명(한글·영문, 부분 일치) 또는 6자리 종목코드 \| Company name (partial) or 6-digit stock code |
| `listed_only` | boolean |  | `False` | 상장사(종목코드 있는 회사)만 \| Only listed companies (default: false) |
| `limit` | integer |  | `20` | 최대 결과 수 (기본값: 20) |

### `get_company`

DART 고유번호로 기업 개황(정식명칭, 대표자, 법인등록번호, 사업자등록번호, 주소, 설립일, 결산월 등)을 조회합니다. | Get a company profile by corp_code.

Returns corp_name, corp_name_eng, stock_code, ceo_nm, corp_cls/corp_cls_name, jurir_no (13-digit
corporate registration number — usable as crno in fsc-financial-info tools), bizr_no, adres,
hm_url, induty_code, est_dt, acc_mt.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `corp_code` | string | 예 |  | DART 고유번호 (8자리 숫자; 모르면 find_corp_code 로 조회) \| DART corp_code (8 digits) |

### `get_disclosure_document`

공시 원문을 텍스트로 조회합니다. 사업보고서는 수십만 자라 offset/max_chars 로 나눠 읽습니다. | Get the full text of a disclosure document, paged by offset/max_chars.

Returns rcept_no, file_name, attachment_files, text, offset, next_offset, total_chars, truncated.
When truncated is true, call again with offset=next_offset (the document is cached in-process,
so paging does not re-download it).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `rcept_no` | string | 예 |  | 접수번호 (14자리; list_disclosures 의 rcept_no) \| Receipt number |
| `offset` | integer |  | `0` | 본문 시작 문자 위치 (기본값: 0) |
| `max_chars` | integer |  | `20000` | 돌려줄 최대 문자 수 (기본값: 20000) |

### `get_financial_statements`

정기보고서의 전체 재무제표를 XBRL 계정 단위로 조회합니다 (재무상태표·손익계산서·포괄손익계산서·현금흐름표·자본변동표). | Get full financial statements (all XBRL account lines).

Returns items (sj_div, account_id, account_nm, thstrm_amount, frmtrm_amount, bfefrmtrm_amount,
thstrm_add_amount for quarterly cumulative, currency). Amounts are integers in KRW.
A full annual report is ~200 rows; pass sj_div to keep the response small.
Listed companies from business year 2015 onward only.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `corp_code` | string | 예 |  | DART 고유번호 (8자리 숫자; 모르면 find_corp_code 로 조회) \| DART corp_code (8 digits) |
| `bsns_year` | string | 예 |  | 사업연도 YYYY (예: 2024). 2015년 이후만 제공 \| Business year |
| `reprt_code` | string |  | `11011` | 보고서 코드: 11011 사업보고서(기본), 11012 반기보고서, 11013 1분기보고서, 11014 3분기보고서 \| Report type |
| `fs_div` | string |  | `CFS` | CFS 연결재무제표(기본) / OFS 별도재무제표 \| Consolidated or separate |
| `sj_div` | string (optional) |  |  | 재무제표 종류로 필터: BS 재무상태표, IS 손익계산서, CIS 포괄손익계산서, CF 현금흐름표, SCE 자본변동표 (생략 시 전부) \| Statement type filter |

### `get_key_accounts`

정기보고서의 주요 재무계정(자산·부채·자본 총계, 매출액, 영업이익, 당기순이익 등)을 당기·전기·전전기로 조회합니다. | Get key financial accounts (assets, liabilities, equity, revenue, operating income, net income) for the current and two prior periods.

Returns items (fs_div, sj_div, account_nm, thstrm_amount, frmtrm_amount, bfefrmtrm_amount,
thstrm_dt, currency). Amounts are integers in KRW. Roughly 20–30 rows; use
get_financial_statements for every account line.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `corp_code` | string | 예 |  | DART 고유번호 (8자리 숫자; 모르면 find_corp_code 로 조회) \| DART corp_code (8 digits) |
| `bsns_year` | string | 예 |  | 사업연도 YYYY (예: 2024). 2015년 이후만 제공 \| Business year |
| `reprt_code` | string |  | `11011` | 보고서 코드: 11011 사업보고서(기본), 11012 반기보고서, 11013 1분기보고서, 11014 3분기보고서 \| Report type |
| `fs_div` | string (optional) |  |  | CFS 연결재무제표 / OFS 별도재무제표 (생략 시 둘 다) \| Consolidated or separate |

### `list_disclosures`

공시 목록을 조회합니다 (접수일 내림차순). 사업보고서·주요사항보고서·지분공시 등의 접수번호를 얻는 데 씁니다. | List DART disclosures (newest first).

Returns items (rcept_no, corp_name, report_nm, flr_nm, rcept_dt, rm), page_no, page_count,
total_count, total_page. Pass rcept_no to get_disclosure_document for the full text.
Without corp_code the date range must be 3 months or less (API limit). Omitting bgn_de
searches the last year (with corp_code) or last 30 days (without), counted back from end_de.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `corp_code` | string (optional) |  |  | DART 고유번호 (8자리 숫자; 모르면 find_corp_code 로 조회) \| DART corp_code (8 digits) |
| `bgn_de` | string (optional) |  |  | 검색 시작 접수일 YYYYMMDD (생략 시 corp_code 있으면 1년 전, 없으면 30일 전) \| Start date |
| `end_de` | string (optional) |  |  | 검색 종료 접수일 YYYYMMDD (생략 시 오늘) \| End date |
| `pblntf_ty` | string (optional) |  |  | 공시유형: A 정기공시, B 주요사항보고, C 발행공시, D 지분공시, E 기타공시, F 외부감사관련, G 펀드공시, H 자산유동화, I 거래소공시, J 공정위공시 \| Disclosure type |
| `page_no` | integer |  | `1` | 페이지 번호 (기본값: 1) |
| `page_count` | integer |  | `10` | 한 페이지 결과 수 (기본값: 10, 최대 100) |

<!-- tools:end -->
