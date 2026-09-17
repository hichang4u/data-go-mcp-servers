"""공용 fixture — OpenDART 실응답 (삼성전자 00126380, 2025-09 수집) 을 줄인 것.

ZIP 응답(corpCode.xml, document.xml)은 실제 파일 구조(파일명, HTML 골격)를 본떠 작게 만든다.
"""

import io
import zipfile

import pytest


BASE = "https://opendart.fss.or.kr/api"


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    # data.go.kr 공통 키는 DART 에 쓰이면 안 되므로 일부러 다른 값으로 둔다.
    monkeypatch.setenv("API_KEY", "data-go-key")
    monkeypatch.setenv("DART_DISCLOSURE_API_KEY", "dart-test-key")


# -- JSON 응답 ------------------------------------------------------------------

COMPANY = {
    "status": "000",
    "message": "정상",
    "corp_code": "00126380",
    "corp_name": "삼성전자(주)",
    "corp_name_eng": "SAMSUNG ELECTRONICS CO,.LTD",
    "stock_name": "삼성전자",
    "stock_code": "005930",
    "ceo_nm": "전영현, 노태문",
    "corp_cls": "Y",
    "jurir_no": "1301110006246",
    "bizr_no": "1248100998",
    "adres": "경기도 수원시 영통구  삼성로 129 (매탄동)",
    "hm_url": "www.samsung.com/sec",
    "ir_url": "",
    "phn_no": "02-2255-0114",
    "fax_no": "031-200-7538",
    "induty_code": "264",
    "est_dt": "19690113",
    "acc_mt": "12",
}

DISCLOSURE_LIST = {
    "status": "000",
    "message": "정상",
    "page_no": 1,
    "page_count": 5,
    "total_count": 49,
    "total_page": 10,
    "list": [
        {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
            "report_nm": "대표이사(대표집행임원)변경(안내공시)              ",
            "rcept_no": "20250325800172",
            "flr_nm": "삼성전자",
            "rcept_dt": "20250325",
            "rm": "유",
        },
        {
            "corp_code": "00126380",
            "corp_name": "삼성전자",
            "stock_code": "005930",
            "corp_cls": "Y",
            "report_nm": "최대주주등소유주식변동신고서              ",
            "rcept_no": "20250321801930",
            "flr_nm": "삼성전자",
            "rcept_dt": "20250321",
            "rm": "유",
        },
    ],
}

NO_DATA = {"status": "013", "message": "조회된 데이타가 없습니다."}

KEY_ACCOUNTS = {
    "status": "000",
    "message": "정상",
    "list": [
        {
            "rcept_no": "20250311001085",
            "reprt_code": "11011",
            "bsns_year": "2024",
            "corp_code": "00126380",
            "stock_code": "005930",
            "fs_div": "CFS",
            "fs_nm": "연결재무제표",
            "sj_div": "BS",
            "sj_nm": "재무상태표",
            "account_nm": "자산총계",
            "thstrm_nm": "제 56 기",
            "thstrm_dt": "2024.12.31 현재",
            "thstrm_amount": "514,531,948,000,000",
            "frmtrm_nm": "제 55 기",
            "frmtrm_dt": "2023.12.31 현재",
            "frmtrm_amount": "455,905,980,000,000",
            "bfefrmtrm_nm": "제 54 기",
            "bfefrmtrm_dt": "2022.12.31 현재",
            "bfefrmtrm_amount": "448,424,507,000,000",
            "ord": "5",
            "currency": "KRW",
        },
        {
            "rcept_no": "20250311001085",
            "reprt_code": "11011",
            "bsns_year": "2024",
            "corp_code": "00126380",
            "stock_code": "005930",
            "fs_div": "CFS",
            "fs_nm": "연결재무제표",
            "sj_div": "IS",
            "sj_nm": "손익계산서",
            "account_nm": "매출액",
            "thstrm_nm": "제 56 기",
            "thstrm_dt": "2024.01.01 ~ 2024.12.31",
            "thstrm_amount": "300,870,903,000,000",
            "frmtrm_nm": "제 55 기",
            "frmtrm_dt": "2023.01.01 ~ 2023.12.31",
            "frmtrm_amount": "258,935,494,000,000",
            "bfefrmtrm_nm": "제 54 기",
            "bfefrmtrm_dt": "2022.01.01 ~ 2022.12.31",
            "bfefrmtrm_amount": "302,231,360,000,000",
            "ord": "23",
            "currency": "KRW",
        },
        {
            "rcept_no": "20250311001085",
            "reprt_code": "11011",
            "bsns_year": "2024",
            "corp_code": "00126380",
            "stock_code": "005930",
            "fs_div": "OFS",
            "fs_nm": "재무제표",
            "sj_div": "BS",
            "sj_nm": "재무상태표",
            "account_nm": "유동자산",
            "thstrm_nm": "제 56 기",
            "thstrm_dt": "2024.12.31 현재",
            "thstrm_amount": "82,320,322,000,000",
            "frmtrm_nm": "제 55 기",
            "frmtrm_dt": "2023.12.31 현재",
            "frmtrm_amount": "68,548,442,000,000",
            "bfefrmtrm_nm": "제 54 기",
            "bfefrmtrm_dt": "2022.12.31 현재",
            "bfefrmtrm_amount": "59,062,658,000,000",
            "ord": "2",
            "currency": "KRW",
        },
    ],
}

FS_ALL = {
    "status": "000",
    "message": "정상",
    "list": [
        {
            "rcept_no": "20250311001085",
            "reprt_code": "11011",
            "bsns_year": "2024",
            "corp_code": "00126380",
            "sj_div": "BS",
            "sj_nm": "재무상태표",
            "account_id": "ifrs-full_Assets",
            "account_nm": "자산총계",
            "account_detail": "-",
            "thstrm_nm": "제 56 기",
            "thstrm_amount": "514531948000000",
            "frmtrm_nm": "제 55 기",
            "frmtrm_amount": "455905980000000",
            "bfefrmtrm_nm": "제 54 기",
            "bfefrmtrm_amount": "448424507000000",
            "ord": "7",
            "currency": "KRW",
        },
        {
            "rcept_no": "20250311001085",
            "reprt_code": "11011",
            "bsns_year": "2024",
            "corp_code": "00126380",
            "sj_div": "IS",
            "sj_nm": "손익계산서",
            "account_id": "dart_OperatingIncomeLoss",
            "account_nm": "영업이익",
            "account_detail": "-",
            "thstrm_nm": "제 56 기",
            "thstrm_amount": "32725961000000",
            "thstrm_add_amount": "",
            "frmtrm_nm": "제 55 기",
            "frmtrm_amount": "6566976000000",
            "bfefrmtrm_nm": "제 54 기",
            "bfefrmtrm_amount": "43376630000000",
            "ord": "6",
            "currency": "KRW",
        },
        {
            "rcept_no": "20250311001085",
            "reprt_code": "11011",
            "bsns_year": "2024",
            "corp_code": "00126380",
            "sj_div": "IS",
            "sj_nm": "손익계산서",
            "account_id": "ifrs-full_ProfitLoss",
            "account_nm": "당기순이익",
            "account_detail": "-",
            "thstrm_nm": "제 56 기",
            "thstrm_amount": "34451351000000",
            "thstrm_add_amount": "",
            "frmtrm_nm": "제 55 기",
            "frmtrm_amount": "15487100000000",
            "bfefrmtrm_nm": "제 54 기",
            "bfefrmtrm_amount": "55654077000000",
            "ord": "18",
            "currency": "KRW",
        },
        {
            "rcept_no": "20250311001085",
            "reprt_code": "11011",
            "bsns_year": "2024",
            "corp_code": "00126380",
            "sj_div": "IS",
            "sj_nm": "손익계산서",
            "account_id": "ifrs-full_Revenue",
            "account_nm": "매출액",
            "account_detail": "-",
            "thstrm_nm": "제 56 기",
            "thstrm_amount": "300870903000000",
            "thstrm_add_amount": "",
            "frmtrm_nm": "제 55 기",
            "frmtrm_amount": "258935494000000",
            "bfefrmtrm_nm": "제 54 기",
            "bfefrmtrm_amount": "302231360000000",
            "ord": "23",
            "currency": "KRW",
        },
        {
            "rcept_no": "20250311001085",
            "reprt_code": "11011",
            "bsns_year": "2024",
            "corp_code": "00126380",
            "sj_div": "CIS",
            "sj_nm": "포괄손익계산서",
            "account_id": "ifrs-full_ComprehensiveIncome",
            "account_nm": "총포괄손익",
            "account_detail": "-",
            "thstrm_nm": "제 56 기",
            "thstrm_amount": "51296338000000",
            "thstrm_add_amount": "",
            "frmtrm_nm": "제 55 기",
            "frmtrm_amount": "18837411000000",
            "bfefrmtrm_nm": "제 54 기",
            "bfefrmtrm_amount": "59659741000000",
            "ord": "6",
            "currency": "KRW",
        },
        {
            "rcept_no": "20250311001085",
            "reprt_code": "11011",
            "bsns_year": "2024",
            "corp_code": "00126380",
            "sj_div": "CIS",
            "sj_nm": "포괄손익계산서",
            "account_id": "ifrs-full_ProfitLoss",
            "account_nm": "당기순이익",
            "account_detail": "-",
            "thstrm_nm": "제 56 기",
            "thstrm_amount": "34451351000000",
            "thstrm_add_amount": "",
            "frmtrm_nm": "제 55 기",
            "frmtrm_amount": "15487100000000",
            "bfefrmtrm_nm": "제 54 기",
            "bfefrmtrm_amount": "55654077000000",
            "ord": "19",
            "currency": "KRW",
        },
        {
            "rcept_no": "20250311001085",
            "reprt_code": "11011",
            "bsns_year": "2024",
            "corp_code": "00126380",
            "sj_div": "CF",
            "sj_nm": "현금흐름표",
            "account_id": "dart_CashAndCashEquivalentsAtBeginningOfPeriodCf",
            "account_nm": "기초현금및현금성자산",
            "account_detail": "-",
            "thstrm_nm": "제 56 기",
            "thstrm_amount": "69080893000000",
            "frmtrm_nm": "제 55 기",
            "frmtrm_amount": "49680710000000",
            "bfefrmtrm_nm": "제 54 기",
            "bfefrmtrm_amount": "39031415000000",
            "ord": "2",
            "currency": "KRW",
        },
    ],
}

# 인증키 오류 (미등록 키). 상태 200 으로 온다.
BAD_KEY = {"status": "010", "message": "등록되지 않은 인증키입니다."}

# corp_code 없이 3개월 초과 조회
PERIOD_TOO_LONG = {
    "status": "100",
    "message": "corp_code가 없는 경우 검색기간은 3개월만 가능합니다.",
}


@pytest.fixture
def bad_key_response() -> dict:
    return BAD_KEY


@pytest.fixture
def period_too_long_response() -> dict:
    return PERIOD_TOO_LONG


@pytest.fixture
def company_response() -> dict:
    return COMPANY


@pytest.fixture
def disclosure_list_response() -> dict:
    return DISCLOSURE_LIST


@pytest.fixture
def no_data_response() -> dict:
    return NO_DATA


@pytest.fixture
def key_accounts_response() -> dict:
    return KEY_ACCOUNTS


@pytest.fixture
def fs_all_response() -> dict:
    return FS_ALL


# -- ZIP 응답 --------------------------------------------------------------------

# 실제 CORPCODE.xml 의 구조. stock_code 는 비상장이면 공백 한 칸.
CORPCODE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<result>
    <list>
        <corp_code>00434003</corp_code>
        <corp_name>다코</corp_name>
        <corp_eng_name>Daco corporation</corp_eng_name>
        <stock_code> </stock_code>
        <modify_date>20170630</modify_date>
    </list>
    <list>
        <corp_code>00126380</corp_code>
        <corp_name>삼성전자</corp_name>
        <corp_eng_name>SAMSUNG ELECTRONICS CO,.LTD</corp_eng_name>
        <stock_code>005930</stock_code>
        <modify_date>20251201</modify_date>
    </list>
    <list>
        <corp_code>00258801</corp_code>
        <corp_name>삼성전자서비스</corp_name>
        <corp_eng_name>SAMSUNG ELECTRONICS SERVICE CO.,LTD.</corp_eng_name>
        <stock_code> </stock_code>
        <modify_date>20240515</modify_date>
    </list>
</result>
"""


def make_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


@pytest.fixture
def corpcode_zip() -> bytes:
    return make_zip({"CORPCODE.xml": CORPCODE_XML.encode("utf-8")})


# document.xml: 본문 <rcept_no>.xml 과 첨부 <rcept_no>_NNNNN.xml 이 한 ZIP 에. 본문은 HTML 이고
# meta 는 euc-kr 이라 하지만 실제 바이트는 UTF-8.
DOCUMENT_HTML = """<html>
 <head>
  <meta content="text/html; charset=euc-kr" http-equiv="Content-Type">
  <STYLE>
.xforms * { font-family: 돋움체;}
  </STYLE>
  <script>var x = 1;</script>
 </head>
 <body>
  <div class="xforms_title">대표이사 변경</div>
  <table><tr><td>변경 전</td><td>한종희</td></tr>
  <tr><td>변경 후</td><td>전영현, 노태문</td></tr></table>
  <p>기타 &amp; 참고사항 &lt;없음&gt;</p>
 </body>
</html>
"""

ATTACHMENT_HTML = "<html><body>감사보고서 첨부</body></html>"


@pytest.fixture
def document_zip() -> bytes:
    return make_zip(
        {
            "20250325800172_00001.xml": ATTACHMENT_HTML.encode("utf-8"),
            "20250325800172.xml": DOCUMENT_HTML.encode("utf-8"),
        }
    )


# ZIP 엔드포인트의 오류는 XML 로 온다 (HTTP 200).
DOCUMENT_ERROR_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    "<result><status>013</status><message>접수번호 오류 : 00000000000000</message></result>"
)


@pytest.fixture
def document_error_xml() -> str:
    return DOCUMENT_ERROR_XML
