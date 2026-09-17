"""기업 고유번호(corp_code) 스냅샷.

OpenDART 는 회사명 검색 API 가 없고, ``corpCode.xml`` 이 전체 기업(약 12만 개) 목록을 ZIP(안에 30MB XML)으로
준다. 매번 받기엔 크므로 파싱 결과를 ``corp_codes.json.gz`` 로 패키지에 동봉하고, 검색은 그 위에서 한다.
갱신은 ``scripts/harvest_dart_corp_codes.py``.

스냅샷 형식: ``{"generated": "YYYYMMDD", "items": [[corp_code, corp_name, stock_code, corp_eng_name], ...]}``.
비상장은 stock_code 가 ``""``, corp_eng_name 은 상장사만 채운다 (크기 절약).
"""

import gzip
import io
import json
import re
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any, Optional, TypedDict
from xml.etree import ElementTree as ET


SNAPSHOT_FILE = "corp_codes.json.gz"


class CorpCodeEntry(TypedDict):
    """기업 한 곳. 비상장은 stock_code 가 빈 문자열."""

    corp_code: str
    corp_name: str
    stock_code: str
    corp_eng_name: str


@dataclass(frozen=True)
class Snapshot:
    """동봉 스냅샷: 생성일(YYYYMMDD)과 전체 항목."""

    generated: str
    entries: list[CorpCodeEntry]


# -- CORPCODE.xml ------------------------------------------------------------


def parse_corp_code_xml(data: bytes) -> list[CorpCodeEntry]:
    """CORPCODE.xml 바이트 → 항목 리스트. 30MB 라 iterparse 로 훑는다."""
    entries: list[CorpCodeEntry] = []
    for _event, element in ET.iterparse(io.BytesIO(data)):
        if element.tag != "list":
            continue
        entries.append(
            {
                "corp_code": (element.findtext("corp_code") or "").strip(),
                "corp_name": (element.findtext("corp_name") or "").strip(),
                "stock_code": (element.findtext("stock_code") or "").strip(),
                "corp_eng_name": (element.findtext("corp_eng_name") or "").strip(),
            }
        )
        element.clear()
    return entries


def parse_corp_code_zip(data: bytes) -> list[CorpCodeEntry]:
    """corpCode.xml 엔드포인트가 주는 ZIP(CORPCODE.xml 하나) → 항목 리스트."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        (name,) = archive.namelist()
        return parse_corp_code_xml(archive.read(name))


# -- 스냅샷 --------------------------------------------------------------------


def dump_snapshot(entries: list[CorpCodeEntry], generated: str) -> bytes:
    """스냅샷 파일 바이트. 영문명은 상장사만 남긴다."""
    rows = [
        [
            e["corp_code"],
            e["corp_name"],
            e["stock_code"],
            e["corp_eng_name"] if e["stock_code"] else "",
        ]
        for e in entries
    ]
    payload = json.dumps(
        {"generated": generated, "items": rows}, ensure_ascii=False, separators=(",", ":")
    )
    return gzip.compress(payload.encode("utf-8"), mtime=0)


def _rows_to_entries(rows: list[list[str]]) -> list[CorpCodeEntry]:
    return [
        {"corp_code": code, "corp_name": name, "stock_code": stock, "corp_eng_name": eng}
        for code, name, stock, eng in rows
    ]


@lru_cache(maxsize=1)
def load_snapshot() -> Snapshot:
    """동봉된 스냅샷을 읽는다 (한 번만, 약 0.1초)."""
    raw = resources.files(__package__).joinpath(SNAPSHOT_FILE).read_bytes()
    data: dict[str, Any] = json.loads(gzip.decompress(raw).decode("utf-8"))
    return Snapshot(generated=str(data["generated"]), entries=_rows_to_entries(data["items"]))


# -- 검색 ----------------------------------------------------------------------

_WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _WS.sub("", text).casefold()


def search_corp_codes(
    query: str,
    entries: Optional[list[CorpCodeEntry]] = None,
    *,
    listed_only: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    """회사명(한/영, 부분 일치) 또는 종목코드로 검색. 정확 일치 > 접두 > 부분, 상장사 우선."""
    q = _norm(query)
    if not q:
        raise ValueError("query 는 비울 수 없습니다")
    if entries is None:
        entries = load_snapshot().entries

    ranked: list[tuple[int, int, int, CorpCodeEntry]] = []
    for entry in entries:
        if listed_only and not entry["stock_code"]:
            continue
        name = _norm(entry["corp_name"])
        eng = _norm(entry["corp_eng_name"])
        if q == name or q == entry["stock_code"]:
            rank = 0
        elif name.startswith(q):
            rank = 1
        elif q in name:
            rank = 2
        elif eng and (eng == q or eng.startswith(q)):
            rank = 3
        elif eng and q in eng:
            rank = 4
        else:
            continue
        ranked.append((rank, 0 if entry["stock_code"] else 1, len(name), entry))

    ranked.sort(key=lambda r: r[:3])
    return {"items": [r[3] for r in ranked[:limit]], "total_count": len(ranked)}
