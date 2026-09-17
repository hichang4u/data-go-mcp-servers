"""API client for 금융감독원 전자공시시스템 OpenDART (https://opendart.fss.or.kr).

OpenDART 는 data.go.kr 계열이 아니다:

- 키 파라미터는 ``crtfc_key``, 키는 opendart.fss.or.kr 에서 따로 발급 (``API_KEY`` fallback 없음)
- 응답은 ``{"status": "000", "message": "정상", ...}`` 평면 구조. ``013`` 은 "조회된 데이타가 없습니다"
- ``corpCode.xml`` / ``document.xml`` 은 ZIP 바이너리, 오류일 때만 XML ``<result><status>``
- 일 호출 한도 20,000건 (키당)
"""

import datetime as dt
import html
import io
import re
import zipfile
from collections import OrderedDict
from typing import Any, Optional
from xml.etree import ElementTree as ET

from data_go_mcp.core import BaseDataGoClient, DataGoAPIError

from .corp_codes import CorpCodeEntry, parse_corp_code_xml
from .models import (
    FS_DIVS,
    PBLNTF_TYPES,
    REPRT_CODES,
    SJ_DIVS,
    Company,
    Disclosure,
    FinancialStatementItem,
    KeyAccount,
)


SOURCE = "OpenDART"
NO_DATA = "013"
MAX_PAGE_COUNT = 100
DOCUMENT_CACHE_SIZE = 4  # 원문은 페이지마다 다시 받지 않도록 프로세스 안에서 몇 건 기억한다

# rcept_no → get_document 결과. 서버는 툴 호출마다 클라이언트를 새로 만들므로 모듈 수준.
_document_cache: "OrderedDict[str, dict[str, Any]]" = OrderedDict()

_DATE = re.compile(r"^\d{8}$")
_CORP_CODE = re.compile(r"^\d{8}$")
_RCEPT_NO = re.compile(r"^\d{14}$")
_YEAR = re.compile(r"^\d{4}$")

# HTML → 텍스트. DART 원문은 HTML(사업보고서는 수 MB) 이라 style/script 를 통째로 버리고 태그를 뗀다.
_DROP_BLOCKS = re.compile(r"<(style|script)\b.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\r\f\v\xa0]+")
_BLANK_LINES = re.compile(r"\n\s*\n+")


def _require(pattern: re.Pattern[str], value: str, name: str, hint: str) -> str:
    if not pattern.match(value or ""):
        raise ValueError(f"{name} 은(는) {hint} 이어야 합니다: {value!r}")
    return value


def _choice(value: Optional[str], choices: dict[str, str], name: str) -> Optional[str]:
    if value is not None and value not in choices:
        raise ValueError(f"{name} 은(는) {', '.join(choices)} 중 하나여야 합니다: {value!r}")
    return value


def default_bgn_de(*, has_corp_code: bool, today: Optional[dt.date] = None) -> str:
    """bgn_de 기본값. API 는 생략하면 당일만 검색하므로 회사 지정 시 1년, 아니면 1개월 전으로 잡는다.

    corp_code 없이는 3개월까지만 허용되므로 여유 있게 30일. ``today`` 자리에 end_de 를 주면 그 날 기준.
    """
    today = today or dt.date.today()
    delta = dt.timedelta(days=365 if has_corp_code else 30)
    return (today - delta).strftime("%Y%m%d")


def clear_document_cache() -> None:
    """원문 캐시를 비운다 (테스트용)."""
    _document_cache.clear()


def html_to_text(markup: str) -> str:
    """태그·style·script 제거, 엔티티 복원, 공백 정리."""
    text = _DROP_BLOCKS.sub(" ", markup)
    text = _TAGS.sub(" ", text)
    text = html.unescape(text)
    lines = [_WS.sub(" ", line).strip() for line in text.splitlines()]
    return _BLANK_LINES.sub("\n", "\n".join(lines)).strip()


class DartDisclosureAPIClient(BaseDataGoClient):
    """OpenDART 클라이언트."""

    base_url = "https://opendart.fss.or.kr/api"
    key_env_prefix = "DART_DISCLOSURE"
    key_param = "crtfc_key"
    shared_key = False
    key_url = "https://opendart.fss.or.kr"

    def _check_response(self, data: dict[str, Any]) -> dict[str, Any]:
        status = str(data.get("status", "000"))
        if status == NO_DATA:
            return {"list": []}
        if status != "000":
            raise DataGoAPIError(status, str(data.get("message", "")), source=SOURCE)
        return data

    async def _get_zip(self, endpoint: str, params: dict[str, Any]) -> zipfile.ZipFile:
        """ZIP 을 주는 엔드포인트. 오류는 XML 로 오므로 여기서 잡는다."""
        response = await self.http.get(self._url(endpoint), params=self._params(params))
        response.raise_for_status()
        content = response.content
        if content.startswith(b"PK"):
            return zipfile.ZipFile(io.BytesIO(content))
        try:
            root = ET.fromstring(content)
            status = root.findtext("status") or "999"
            message = root.findtext("message") or ""
        except ET.ParseError:
            status, message = "999", content[:200].decode("utf-8", "replace")
        raise DataGoAPIError(status, message, source=SOURCE)

    # -- 회사 --------------------------------------------------------------

    async def get_company(self, corp_code: str) -> Optional[dict[str, Any]]:
        """기업 개황 (company.json). 없는 고유번호면 None."""
        _require(_CORP_CODE, corp_code, "corp_code", "8자리 숫자")
        data = await self.get("company.json", {"corp_code": corp_code})
        if not data.get("corp_code"):
            return None
        data.pop("status", None)
        data.pop("message", None)
        return Company(**data).model_dump()

    # -- 공시 목록 ------------------------------------------------------------

    async def list_disclosures(
        self,
        corp_code: Optional[str] = None,
        bgn_de: Optional[str] = None,
        end_de: Optional[str] = None,
        pblntf_ty: Optional[str] = None,
        page_no: int = 1,
        page_count: int = 10,
    ) -> dict[str, Any]:
        """공시 목록 (list.json). corp_code 없이는 기간이 3개월 이내여야 한다 (API 제한).

        bgn_de 를 생략하면 API 가 당일만 검색하므로 ``default_bgn_de`` 로 채운다.
        """
        if corp_code is not None:
            _require(_CORP_CODE, corp_code, "corp_code", "8자리 숫자")
        if end_de is not None:
            _require(_DATE, end_de, "end_de", "YYYYMMDD")
        if bgn_de is None:
            anchor = dt.datetime.strptime(end_de, "%Y%m%d").date() if end_de else None
            bgn_de = default_bgn_de(has_corp_code=corp_code is not None, today=anchor)
        _require(_DATE, bgn_de, "bgn_de", "YYYYMMDD")
        if end_de is not None and bgn_de > end_de:
            raise ValueError(f"bgn_de({bgn_de}) 가 end_de({end_de}) 보다 늦습니다")
        _choice(pblntf_ty, PBLNTF_TYPES, "pblntf_ty")
        if page_no < 1:
            raise ValueError(f"page_no 는 1 이상이어야 합니다: {page_no}")
        if not 1 <= page_count <= MAX_PAGE_COUNT:
            raise ValueError(f"page_count 는 1~{MAX_PAGE_COUNT} 이어야 합니다: {page_count}")

        data = await self.get(
            "list.json",
            {
                "corp_code": corp_code,
                "bgn_de": bgn_de,
                "end_de": end_de,
                "pblntf_ty": pblntf_ty,
                "page_no": page_no,
                "page_count": page_count,
            },
        )
        items = [Disclosure(**row).model_dump() for row in data.get("list") or []]
        return {
            "items": items,
            "page_no": int(data.get("page_no", page_no)),
            "page_count": int(data.get("page_count", page_count)),
            "total_count": int(data.get("total_count", 0)),
            "total_page": int(data.get("total_page", 0)),
        }

    # -- 재무제표 ------------------------------------------------------------

    def _fs_params(self, corp_code: str, bsns_year: str, reprt_code: str) -> dict[str, Any]:
        _require(_CORP_CODE, corp_code, "corp_code", "8자리 숫자")
        _require(_YEAR, bsns_year, "bsns_year", "YYYY")
        _choice(reprt_code, REPRT_CODES, "reprt_code")
        return {"corp_code": corp_code, "bsns_year": bsns_year, "reprt_code": reprt_code}

    async def get_key_accounts(
        self,
        corp_code: str,
        bsns_year: str,
        reprt_code: str = "11011",
        fs_div: Optional[str] = None,
    ) -> dict[str, Any]:
        """주요계정 (fnlttSinglAcnt.json): 연결·별도의 재무상태표·손익계산서 주요 항목. fs_div 는 클라이언트 필터."""
        params = self._fs_params(corp_code, bsns_year, reprt_code)
        _choice(fs_div, FS_DIVS, "fs_div")
        data = await self.get("fnlttSinglAcnt.json", params)
        items = [KeyAccount(**row).model_dump() for row in data.get("list") or []]
        if fs_div:
            items = [i for i in items if i["fs_div"] == fs_div]
        return {**params, "items": items}

    async def get_financial_statements(
        self,
        corp_code: str,
        bsns_year: str,
        reprt_code: str = "11011",
        fs_div: str = "CFS",
        sj_div: Optional[str] = None,
    ) -> dict[str, Any]:
        """전체 재무제표 (fnlttSinglAcntAll.json). sj_div 는 클라이언트 필터. 2015년 이후 상장사만."""
        params = self._fs_params(corp_code, bsns_year, reprt_code)
        _choice(fs_div, FS_DIVS, "fs_div")
        _choice(sj_div, SJ_DIVS, "sj_div")
        data = await self.get("fnlttSinglAcntAll.json", {**params, "fs_div": fs_div})
        items = [FinancialStatementItem(**row).model_dump() for row in data.get("list") or []]
        if sj_div:
            items = [i for i in items if i["sj_div"] == sj_div]
        return {**params, "fs_div": fs_div, "items": items}

    # -- 원문 -----------------------------------------------------------------

    async def get_document(self, rcept_no: str) -> dict[str, Any]:
        """공시 원문 (document.xml). ZIP 안의 ``<rcept_no>.xml`` (HTML) 을 텍스트로 바꾼다.

        사업보고서는 수 MB 라 최근 ``DOCUMENT_CACHE_SIZE`` 건은 프로세스 안에 캐시한다 (페이징용).
        """
        _require(_RCEPT_NO, rcept_no, "rcept_no", "14자리 숫자")
        cached = _document_cache.get(rcept_no)
        if cached is not None:
            _document_cache.move_to_end(rcept_no)
            return dict(cached)
        with await self._get_zip("document.xml", {"rcept_no": rcept_no}) as archive:
            names = archive.namelist()
            main = f"{rcept_no}.xml"
            if main not in names:
                main = max(names, key=lambda n: archive.getinfo(n).file_size)
            raw = archive.read(main)
        # meta 는 euc-kr 이라고 하지만 실제로는 UTF-8 인 파일이 대부분이다.
        try:
            markup = raw.decode("utf-8")
        except UnicodeDecodeError:
            markup = raw.decode("cp949", errors="replace")
        doc = {
            "rcept_no": rcept_no,
            "file_name": main,
            "attachment_files": [n for n in names if n != main],
            "text": html_to_text(markup),
        }
        _document_cache[rcept_no] = doc
        while len(_document_cache) > DOCUMENT_CACHE_SIZE:
            _document_cache.popitem(last=False)
        return dict(doc)

    # -- 기업코드 ------------------------------------------------------------

    async def download_corp_codes(self) -> list[CorpCodeEntry]:
        """corpCode.xml (ZIP, 약 3.5MB) 을 받아 파싱한다. 스냅샷 갱신용."""
        with await self._get_zip("corpCode.xml", {}) as archive:
            (name,) = archive.namelist()
            return parse_corp_code_xml(archive.read(name))
