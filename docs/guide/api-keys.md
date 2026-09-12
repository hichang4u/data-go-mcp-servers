# API 키 발급과 활용신청

## 1. 인증키 발급

1. [data.go.kr](https://www.data.go.kr) 회원가입 → 로그인
2. 마이페이지 → **일반 인증키(Decoding)** 값을 복사

키는 하나로 이 저장소의 모든 서버에 쓸 수 있다. 안전보건공단(MSDS)도 같은 키로 호출된다.

Encoding 값(`%2B`, `%3D` 가 섞인 것)이 아니라 **Decoding 값**(`+`, `=` 가 그대로인 것, 보통 `==` 로 끝남)을 써야 한다. Encoding 값을 넣으면 서버가 한 번 더 인코딩해 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`(코드 30)가 난다.

## 2. API 별 활용신청

키가 있어도 **API 마다 활용신청**을 해야 한다. 미신청 상태면 코드 30(`등록되지 않은 서비스키`) 또는 odcloud 계열은 HTTP 401 이 온다. 전부 자동승인이며 신청 직후부터 쓸 수 있다.

| 서버 | 신청 페이지 |
|---|---|
| nps-business-enrollment | [국민연금공단_국민연금 가입 사업장 내역](https://www.data.go.kr/data/3046071/openapi.do) |
| nts-business-verification | 포털에서 "국세청_사업자등록정보 진위확인 및 상태조회 서비스" 검색 |
| pps-narajangteo | 포털에서 "조달청_나라장터 공공데이터개방표준서비스" 검색 |
| fsc-financial-info | [금융위원회_기업 재무정보](https://www.data.go.kr/data/15043459/openapi.do) |
| presidential-speeches | [대통령기록관_대통령연설기록(연설문)](https://www.data.go.kr/data/15084167/fileData.do) → "오픈API" 탭 |
| msds-chemical-info | 별도 신청 없이 동작 확인됨 (2026-09) |

활용목적은 "참고자료" 또는 "앱개발" 정도면 된다. 개발계정 일일 트래픽은 대개 10,000건이다.

## 3. 키를 서버에 넘기는 방법

우선순위:

1. 서버별 변수 `<SERVER>_API_KEY` — 예: `NPS_BUSINESS_ENROLLMENT_API_KEY`
2. 공통 변수 `API_KEY`

보통 `API_KEY` 하나면 된다. 서버별 변수는 API 마다 다른 계정의 키를 써야 할 때만 쓴다.

MCP 클라이언트 설정의 `"env"` 로 넘기는 것이 기본이고, 저장소를 clone 해서 실행할 때는 루트의 `.env` 파일(`API_KEY=…`)도 읽는다.

## 4. 확인

저장소를 clone 했다면 6개 API 를 한 번에 점검할 수 있다:

```bash
uv run python scripts/check_apis.py
```

각 줄의 `resultCode=00` 또는 `status_code OK` 가 정상이다. `30` 이면 그 API 의 활용신청이 안 된 것이다.
