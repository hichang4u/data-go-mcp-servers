"""work24 테스트 공용 fixture — 2026-10-01 실제 응답."""

import pytest


BASE = "https://www.work24.go.kr/cm/openApi/call/wk"

LIST_XML = """<?xml version="1.0" encoding="UTF-8"?><wantedRoot><total>2</total><startPage>1</startPage><display>2</display><wanted><wantedAuthNo>K140022610010052</wantedAuthNo><company>워터매니지먼트주식회사</company><busino>5038169211</busino><indTpNm>폐수 처리업</indTpNm><title>[운영팀] 환경·안전 및 운영관리 담당자 채용</title><salTpNm>연봉</salTpNm><sal>4100만원</sal><minSal>41000000</minSal><maxSal>0</maxSal><region>대구 서구</region><holidayTpNm>주5일근무</holidayTpNm><minEdubg>대졸(4년)</minEdubg><maxEdubg>박사</maxEdubg><career>경력</career><regDt>26-10-01</regDt><closeDt>채용시까지  26-11-30</closeDt><infoSvc>VALIDATION</infoSvc><wantedInfoUrl>https://www.work24.go.kr/wk/a/b/1500/empDetailAuthView.do?wantedAuthNo=K140022610010052</wantedInfoUrl><smodifyDtm>202610011948</smodifyDtm><zipCd>41759</zipCd><basicAddr>대구광역시 서구 와룡로90길 24</basicAddr><detailAddr>워터매니지먼트</detailAddr><empTpCd>10</empTpCd><jobsCd>155500</jobsCd></wanted><wanted><wantedAuthNo>K140022609170041</wantedAuthNo><company>워터매니지먼트주식회사</company><busino>5038169211</busino><indTpNm>폐수 처리업</indTpNm><title>[기술팀] 수질관리 담당자</title><salTpNm>월급</salTpNm><sal>300만원</sal><minSal>3000000</minSal><maxSal>3500000</maxSal><region>대구 서구</region><career>신입</career><regDt>26-09-17</regDt><closeDt>26-10-31</closeDt><infoSvc>VALIDATION</infoSvc><empTpCd>10</empTpCd><jobsCd>155500</jobsCd></wanted></wantedRoot>"""

DETAIL_XML = """<?xml version="1.0" encoding="UTF-8"?><wantedDtl><wantedAuthNo>K140022610010052</wantedAuthNo><corpInfo><corpNm>워터매니지먼트주식회사</corpNm><reperNm>김남진</reperNm><totPsncnt>25 명</totPsncnt><capitalAmt>453 백만원</capitalAmt><yrSalesAmt>5745 백만원</yrSalesAmt><indTpCdNm>폐수 처리업</indTpCdNm><busiCont>산업폐수처리</busiCont><corpAddr>41759 대구광역시 서구 와룡로90길 24 (이현동)</corpAddr><homePg></homePg><busiSize>중소기업</busiSize></corpInfo><wantedInfo><jobsNm>환경공학 기술자 및 연구원(155500)</jobsNm><wantedTitle>[운영팀] 환경·안전 및 운영관리 담당자 채용</wantedTitle><jobCont>폐수처리시설 운영 관련 업무 지원</jobCont><receiptCloseDt>채용시까지</receiptCloseDt><empTpNm>기간의 정함이 없는 근로계약</empTpNm><collectPsncnt>1</collectPsncnt><salTpNm>연봉41,000,000원 이상, 면접 후 재조정 가능</salTpNm><enterTpNm>경력 (최소3년) 필수</enterTpNm><eduNm>대졸(4년)-박사</eduNm><major>환경학</major><certificate>수질환경산업기사,대기환경산업기사</certificate></wantedInfo></wantedDtl>"""

EMPTY_XML = """<?xml version="1.0" encoding="UTF-8"?><wantedRoot><message>정보가 존재하지 않습니다.</message><messageCd>006</messageCd></wantedRoot>"""

DETAIL_ERROR_XML = """<?xml version="1.0" encoding="UTF-8"?><wantedRoot><message>채용정보API의 상세보기 필수항목인 정보제공처가 바르지 않습니다.</message><messageCd>018</messageCd></wantedRoot>"""

SERVICE_ERROR_XML = """<?xml version='1.0' encoding='UTF-8'?><GO24><error>신청하신 OpenApi 서비스가 존재하지 않습니다</error></GO24>"""


@pytest.fixture
def base_url() -> str:
    return BASE


@pytest.fixture
def list_xml() -> str:
    return LIST_XML


@pytest.fixture
def detail_xml() -> str:
    return DETAIL_XML


@pytest.fixture
def empty_xml() -> str:
    return EMPTY_XML


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("WORK24_API_KEY", "test-key")
    monkeypatch.delenv("API_KEY", raising=False)
