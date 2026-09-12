# 국세청 사업자등록정보 진위확인·상태조회 (nts-business-verification)

사업자등록번호가 유효한지, 계속사업자/휴업/폐업 상태와 과세유형이 무엇인지 조회하고, 사업자번호·개업일·대표자명 조합이 국세청 등록정보와 일치하는지 확인한다.

| | |
|---|---|
| 데이터셋 | 국세청_사업자등록정보 진위확인 및 상태조회 서비스 (`api.odcloud.kr/api/nts-businessman/v1`) |
| 활용신청 | 필요 (자동승인) |
| 환경변수 | `API_KEY` 또는 `NTS_BUSINESS_VERIFICATION_API_KEY` |
| 패키지 | `data-go-mcp.nts-business-verification` (`src/nts-business-verification`) |

## 설정

```json
"nts-business-verification": {
  "command": "uvx",
  "args": ["--from", "git+https://github.com/hichang4u/data-go-mcp-servers#subdirectory=src/nts-business-verification", "data-go-mcp.nts-business-verification"],
  "env": { "API_KEY": "<data.go.kr 인증키>" }
}
```

## 예시 프롬프트

- "사업자등록번호 120-88-00767의 현재 상태를 조회해줘"
- "123-45-67890이 2020년 1월 1일에 홍길동 대표로 등록된 것이 맞는지 확인해줘"
- "이 사업자번호 목록의 휴·폐업 여부를 한번에 확인해줘: …"

## 알아둘 것

- 한 번에 최대 100건. 하이픈은 자동으로 제거된다.
- 상태 코드: `01` 계속사업자, `02` 휴업자, `03` 폐업자. 과세유형 코드 `01` 일반과세자, `02` 간이과세자.
- 미등록 번호는 오류가 아니라 `tax_type` 에 "국세청에 등록되지 않은 사업자등록번호입니다." 가 담겨 온다.
- 진위확인 `valid` 는 `01` 일치 / `02` 불일치. 불일치는 정상 응답이며 `status` 가 `null` 이다.

## 툴

<!-- tools:start -->

### `batch_validate_businesses`

여러 사업자등록정보를 한 번에 진위확인합니다. Batch validate business registrations.

Returns request_count, valid_count, results[] (business_number, valid, valid_msg, status).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `businesses_json` | string | 예 |  | JSON 배열 문자열, 최대 100개. 각 항목 필수: b_no, start_dt, p_nm. 선택: p_nm2, b_nm, corp_no, b_sector, b_type, b_adr. 예: [{"b_no": "1234567890", "start_dt": "20200101", "p_nm": "홍길동"}] |

### `check_business_status`

사업자등록 상태를 조회합니다. Check business registration status.

Returns request_count, match_count, businesses[] (status_code 01: 계속사업자, 02: 휴업자,
03: 폐업자; 미등록 번호는 tax_type 에 안내 문구가 온다).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `business_numbers` | string | 예 |  | 사업자등록번호 목록, 쉼표 구분, 최대 100개 (하이픈 허용) |

### `validate_business`

사업자등록정보 진위확인을 수행합니다. Validate business registration information.

Returns business_number, valid (01: 일치, 02: 불일치), valid_msg, status (일치 시 상태 정보).

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|
| `business_number` | string | 예 |  | 사업자등록번호 10자리 (하이픈 허용) |
| `start_date` | string | 예 |  | 개업일자 YYYYMMDD (하이픈 허용) |
| `representative_name` | string | 예 |  | 대표자성명 |
| `representative_name2` | string (optional) |  |  | 대표자성명2 (외국인 한글명) |
| `business_name` | string (optional) |  |  | 상호 |
| `corp_number` | string (optional) |  |  | 법인등록번호 13자리 |
| `business_sector` | string (optional) |  |  | 주업태명 |
| `business_type` | string (optional) |  |  | 주종목명 |
| `business_address` | string (optional) |  |  | 사업장주소 |

<!-- tools:end -->
