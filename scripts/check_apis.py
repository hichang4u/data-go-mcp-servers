"""각 서버가 쓰는 공공 API 중 대표 엔드포인트가 살아 있는지 최소 요청으로 확인한다.

서버가 API 를 여러 개 쓰면(molit 11, nps 3, fsc 3) 전부가 아니라 대표만 본다.

사용법:
    API_KEY=... uv run python scripts/check_apis.py

각 엔드포인트에 가장 가벼운 조회를 한 번 보내고 HTTP 상태와 resultCode를 출력한다.
resultCode 30/31/32 는 키 문제, 12 는 서비스 폐기, HTTP 404 는 엔드포인트 변경을 뜻한다.
"""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv


load_dotenv()

# (서버명, 메서드, URL, 추가 파라미터/바디)
TARGETS = [
    (
        "nps-business-enrollment",
        "GET",
        "https://apis.data.go.kr/B552015/NpsBplcInfoInqireServiceV2/getBassInfoSearchV2",
        {"wkplNm": "삼성전자", "numOfRows": 1, "pageNo": 1, "dataType": "json"},
    ),
    (
        "nps-business-enrollment (법정동코드)",
        "GET",
        "https://apis.data.go.kr/1741000/StanReginCd/getStanReginCdList",
        {"locatadd_nm": "강남구", "numOfRows": 1, "pageNo": 1, "type": "json"},
    ),
    (
        "nps-business-enrollment (고용산재보험)",
        "GET",
        "https://apis.data.go.kr/B490001/gySjbPstateInfoService/getGySjBoheomBsshItem",
        {"v_saeopjaDrno": "1248100998", "opaBoheomFg": "2", "numOfRows": 1, "pageNo": 1},
    ),
    (
        "nts-business-verification",
        "POST",
        "https://api.odcloud.kr/api/nts-businessman/v1/status",
        {"b_no": ["1208800767"]},
    ),
    (
        "pps-narajangteo",
        "GET",
        "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService/getDataSetOpnStdBidPblancInfo",
        {
            "numOfRows": 1,
            "pageNo": 1,
            "type": "json",
            "bidNtceBgnDt": "202501010000",
            "bidNtceEndDt": "202501020000",
        },
    ),
    (
        "pps-narajangteo (조달업체정보)",
        "GET",
        "https://apis.data.go.kr/1230000/ao/UsrInfoService02/getPrcrmntCorpBasicInfo02",
        {"inqryDiv": "3", "bizno": "1118126895", "numOfRows": 1, "pageNo": 1, "type": "json"},
    ),
    (
        "fsc-financial-info (지수시세)",
        "GET",
        "https://apis.data.go.kr/1160100/GetMarketIndexInfoService_V2/getStockMarketIndex_V2",
        {"numOfRows": 1, "pageNo": 1, "resultType": "json", "idxNm": "코스피"},
    ),
    (
        "fsc-financial-info (ETF시세)",
        "GET",
        "https://apis.data.go.kr/1160100/GetSecuritiesProductInfoService_V2/getETFPriceInfo_V2",
        {"numOfRows": 1, "pageNo": 1, "resultType": "json", "likeItmsNm": "KODEX 200"},
    ),
    (
        "molit-realestate (아파트매매)",
        "GET",
        "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev",
        {"LAWD_CD": "11680", "DEAL_YMD": "202608", "numOfRows": 1, "pageNo": 1},
    ),
    (
        "molit-realestate (건축물대장)",
        "GET",
        "https://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo",
        {"sigunguCd": "11680", "bjdongCd": "10500", "bun": "0001", "ji": "0001", "numOfRows": 1},
    ),
    (
        "molit-realestate (아파트전월세)",
        "GET",
        "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent",
        {"LAWD_CD": "11680", "DEAL_YMD": "202608", "numOfRows": 1, "pageNo": 1},
    ),
    (
        "fsc-financial-info",
        "GET",
        "https://apis.data.go.kr/1160100/service/GetFinaStatInfoService_V2/getSummFinaStat_V2",
        {
            "numOfRows": 1,
            "pageNo": 1,
            "resultType": "json",
            "bizYear": "2023",
            "crno": "1301110006246",
        },
    ),
    (
        "fsc-financial-info (기업기본정보)",
        "GET",
        "https://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2/getCorpOutline_V2",
        {"numOfRows": 1, "pageNo": 1, "resultType": "json", "crno": "1301110006246"},
    ),
    (
        "fsc-financial-info (주식시세)",
        "GET",
        "https://apis.data.go.kr/1160100/GetStockSecuritiesInfoService_V2/getStockPriceInfo_V2",
        {"numOfRows": 1, "pageNo": 1, "resultType": "json", "likeSrtnCd": "005930"},
    ),
    (
        "ftc-ecommerce (통신판매사업자)",
        "GET",
        "https://apis.data.go.kr/1130000/MllBsDtl_3Service/getMllBsInfoDetail_3",
        {"brno": "1208800767", "numOfRows": 1, "pageNo": 1, "resultType": "json"},
    ),
    (
        "presidential-speeches",
        "GET",
        "https://api.odcloud.kr/api/15084167/v1/uddi:1c8b5454-bd4e-45db-98f7-fe94d71f271b",
        {"page": 1, "perPage": 1},
    ),
    (
        "msds-chemical-info",
        "GET",
        "https://msds.kosha.or.kr/openapi/service/msdschem/chemlist",
        {"searchWrd": "benzene", "searchCnd": 0, "numOfRows": 1, "pageNo": 1},
    ),
    # OpenDART 는 data.go.kr 키가 아니다 — 키 환경변수와 파라미터 이름을 따로 준다
    (
        "dart-disclosure",
        "GET",
        "https://opendart.fss.or.kr/api/company.json",
        {"corp_code": "00126380"},
        "DART_DISCLOSURE_API_KEY",
        "crtfc_key",
    ),
]


async def check(
    client: httpx.AsyncClient,
    name: str,
    method: str,
    url: str,
    extra: dict,
    key_env: str = "API_KEY",
    key_param: str = "serviceKey",
) -> str:
    """엔드포인트 하나를 호출하고 한 줄 요약을 돌려준다."""
    key = os.getenv(key_env)
    if not key:
        return f"{name:36s} SKIP ({key_env} not set)"
    try:
        if method == "POST":
            r = await client.post(url, params={key_param: key, "returnType": "JSON"}, json=extra)
        else:
            r = await client.get(url, params={key_param: key, **extra})
    except httpx.HTTPError as e:
        return f"{name:36s} NETWORK ERROR {e}"

    body = r.text[:200].replace("\n", " ")
    code = ""
    try:
        data = r.json()
        header = data.get("response", {}).get("header", {})
        code = header.get("resultCode", "") or str(data.get("status_code", ""))
        code = code or str(data.get("status", ""))  # OpenDART: "000" 정상
        if not code and "StanReginCd" in data:  # 법정동코드: head 배열 안의 RESULT
            for entry in data["StanReginCd"][0].get("head", []):
                code = code or entry.get("RESULT", {}).get("resultCode", "")
        if not code and "RESULT" in data:  # 법정동코드: 결과 없음/오류는 최상위 RESULT
            code = data["RESULT"].get("resultCode", "")
    except (ValueError, LookupError, AttributeError, TypeError):
        pass
    return f"{name:36s} HTTP {r.status_code}  resultCode={code or '-':4s}  {body}"


async def check_ecos(client: httpx.AsyncClient) -> str:
    """ECOS 는 인증키가 경로 세그먼트라 따로 확인한다. 키가 없으면 sample 로 생존만 본다."""
    name = "bok-ecos (한국은행 ECOS)"
    key = os.getenv("BOK_ECOS_API_KEY") or "sample"
    suffix = "" if os.getenv("BOK_ECOS_API_KEY") else "  (sample key)"
    try:
        r = await client.get(f"https://ecos.bok.or.kr/api/KeyStatisticList/{key}/json/kr/1/1")
    except httpx.HTTPError as e:
        return f"{name:36s} NETWORK ERROR {e}"
    body = r.text[:200].replace("\n", " ")
    code = "-"
    try:
        data = r.json()
        result = data.get("RESULT")
        code = str(result.get("CODE")) if isinstance(result, dict) else "OK"
    except ValueError:
        pass
    return f"{name:36s} HTTP {r.status_code}  resultCode={code:4s}  {body}{suffix}"


async def main() -> int:
    """모든 대상을 병렬로 확인하고 결과를 출력한다."""
    if not os.getenv("API_KEY"):
        print("API_KEY 환경변수가 필요합니다 (.env 또는 export)", file=sys.stderr)
        return 1
    async with httpx.AsyncClient(timeout=20.0) as client:
        lines = await asyncio.gather(*(check(client, *t) for t in TARGETS))
        for line in [*lines, await check_ecos(client)]:
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
