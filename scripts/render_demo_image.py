"""데모 실행 출력을 README 용 PNG 로 그린다 (브라우저 없이).

사용법:
    uv run python scripts/demo_due_diligence.py > demo.txt
    uv run --with pillow python scripts/render_demo_image.py demo.txt docs/images/demo-due-diligence.png

Pillow 는 이 저장소의 의존성이 아니다 — ``--with pillow`` 로 그때만 끌어 쓴다.
한글이 고정폭인 굴림체(``gulim.ttc``)를 쓰므로 터미널처럼 열이 맞는다.
"""

# Pillow 는 이 저장소에 설치하지 않는다 (``--with pillow``) → pyright 가 import 를 못 찾는다
# pyright: reportMissingImports=false

import argparse
import re
import sys
from pathlib import Path


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

BG = (8, 10, 15)
PANEL = (17, 19, 26)
BAR = (23, 26, 35)
BORDER = (34, 40, 51)
COLORS = {
    "rule": (43, 48, 64),
    "title": (255, 255, 255),
    "agency": (251, 191, 36),
    "tool": (167, 139, 250),
    "time": (107, 114, 128),
    "data": (134, 239, 172),
    "closing": (125, 211, 252),
    "prompt": (107, 114, 128),
    "command": (125, 211, 252),
}
AGENCIES = {
    "국세청",
    "금융위원회",
    "근로복지공단",
    "조달청",
    "금융감독원 DART",
    "조달청 나라장터",
    "국민연금공단 (법정동코드)",
    "국토교통부 (매매)",
    "국토교통부 (전월세)",
    "고용24 (채용공고)",
    "고용24 (공고 상세)",
}

FONT_CANDIDATES = [
    (r"C:\Windows\Fonts\gulim.ttc", 1),  # 굴림체 — 한글 고정폭
    (r"C:\Windows\Fonts\batang.ttc", 1),  # 바탕체
    (r"C:\Windows\Fonts\malgun.ttf", 0),
]


def classify(line: str) -> str:
    """줄 종류로 색을 정한다."""
    stripped = line.strip()
    if stripped and set(stripped) == {"─"}:
        return "rule"
    if stripped in AGENCIES:
        return "agency"
    if stripped.startswith("··"):
        return "tool"
    if re.fullmatch(r"\(\d+\.\d+초\)", stripped):
        return "time"
    if stripped.startswith(("사업자등록번호", "사업자번호")) or any(
        k in stripped for k in ("아파트 실거래", "채용 현황", "낙찰 이력")
    ):
        return "title"
    if any(
        k in stripped
        for k in (
            "개 기관을 한 번에",
            "건을 찾았습니다",
            "실거래를 훑었습니다",
            "회사 규모를 확인했습니다",
        )
    ):
        return "closing"
    return "data"


def load_font(size: int):
    """한글이 되는 고정폭 폰트를 찾는다."""
    from PIL import ImageFont

    for path, index in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size, index=index)
            except OSError:
                continue
    raise SystemExit("한글 고정폭 폰트를 찾지 못했습니다 (gulim.ttc / batang.ttc / malgun.ttf)")


def render(lines: list[str], command: str, out: Path, size: int = 17) -> Path:
    """터미널 모양 PNG 로 그린다."""
    from PIL import Image, ImageDraw

    font = load_font(size)
    bold = load_font(size)
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    line_h = int(size * 1.55)
    pad_x, pad_y = 26, 18
    bar_h = 38
    rows = [command, "", *lines]
    width = max(measure.textlength(row, font=font) for row in rows)
    panel_w = int(width) + pad_x * 2
    panel_h = bar_h + pad_y * 2 + line_h * len(rows)
    margin = 18

    image = Image.new("RGB", (panel_w + margin * 2, panel_h + margin * 2), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (margin, margin, margin + panel_w, margin + panel_h), radius=10, fill=PANEL
    )
    draw.rounded_rectangle((margin, margin, margin + panel_w, margin + bar_h), radius=10, fill=BAR)
    draw.rectangle((margin, margin + bar_h - 10, margin + panel_w, margin + bar_h), fill=BAR)
    draw.line((margin, margin + bar_h, margin + panel_w, margin + bar_h), fill=BORDER, width=1)
    for i, color in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        cx = margin + 18 + i * 18
        cy = margin + bar_h // 2
        draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=color)
    draw.text(
        (margin + 78, margin + bar_h // 2),
        "data-go-mcp-servers",
        font=font,
        fill=(107, 114, 128),
        anchor="lm",
    )

    y = margin + bar_h + pad_y
    x = margin + pad_x
    draw.text((x, y), "$ ", font=font, fill=COLORS["prompt"])
    draw.text(
        (x + measure.textlength("$ ", font=font), y), command, font=bold, fill=COLORS["command"]
    )
    y += line_h * 2

    for line in lines:
        draw.text((x, y), line, font=font, fill=COLORS[classify(line)])
        y += line_h

    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)
    return out


def main() -> int:
    """텍스트 파일을 읽어 PNG 로."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="demo_due_diligence.py 출력 파일")
    parser.add_argument("output", type=Path, help="만들 PNG 경로")
    parser.add_argument(
        "--command",
        default="uv run python scripts/demo_due_diligence.py 214-87-12538",
        help="화면 맨 위에 보여줄 명령",
    )
    args = parser.parse_args()

    lines = args.source.read_text(encoding="utf-8").rstrip("\n").split("\n")
    out = render(lines, args.command, args.output)
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
