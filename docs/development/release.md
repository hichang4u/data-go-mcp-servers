# 릴리스

## 배포 경로

**git 직접 설치**가 기본이다. 사용자는 `uvx --from "git+…#subdirectory=src/<server>" data-go-mcp.<server>` 로 실행하며, uv 가 저장소를 받아 워크스페이스(`[tool.uv.sources] data-go-mcp-core = { workspace = true }`)를 그대로 해석하므로 core 를 따로 배포할 필요가 없다 (2026-09-12 확인).

**Smithery** 에는 통합 서버(`src/all-servers`)가 MCPB 번들 하나로 올라간다 (`hichang4u/data-go-mcp`). 번들(`mcpb/`)에는 코드가 없고 `pyproject.toml` 이 저장소 태그 하나를 가리킨다 — 호스트가 `uv run` 으로 설치·실행한다 (MCPB `server.type: uv`). Smithery 는 `smithery.yaml` 을 더 이상 읽지 않는다 (2026-09-19 문서 기준: URL 또는 MCPB 만).

PyPI 는 쓰지 않는다. 원저장소의 `data-go-mcp.*` 네임스페이스는 우리 것이 아니고, git 설치로 충분하다. 필요해지면 `scripts/deploy_to_pypi.py` (core 를 먼저 올리도록 정렬돼 있음)와 새 네임스페이스를 정한다.

## 버전

- 각 `src/*/pyproject.toml` 의 `version`. 서버는 각자 올린다 — 툴이 바뀐 서버만 bump (v0.12.0 시점: pps 0.7.0, fsc 0.6.0, nps 0.5.0, molit-realestate 0.2.0, dart·all-servers·work24-jobs·ftc-ecommerce 0.1.0, bok-ecos 0.1.1, 나머지 0.3.0), core 는 독립 (0.2.x).
- fsc 의 `SERVER_VERSION` 은 패키지 메타데이터에서 읽으므로 손댈 곳이 없다.
- git 태그 `vX.Y.Z` 는 저장소 전체 스냅샷이며 서버 버전과 무관하게 올라간다. 사용자는 `data-go-mcp-servers@v0.12.0#subdirectory=…` 로 고정할 수 있다.

## 절차

1. `main` 이 green 인지 확인 (CI).
2. `src/*/CHANGELOG.md` 에 항목 추가. 형식은 Keep a Changelog.
3. 버전 bump: `src/*/pyproject.toml` (+ `src/*/data_go_mcp/*/__init__.py` 의 `__version__` 이 있으면 함께).
4. `uv lock` 후 커밋: `chore(release): v0.12.0`.
5. 태그와 릴리스:
   ```bash
   git tag -a v0.12.0 -m "v0.12.0"
   git push origin main --tags
   gh release create v0.12.0 --title "v0.12.0" --notes-file <notes>
   ```
6. 새 환경에서 확인:
   ```bash
   uvx --refresh --from "git+https://github.com/hichang4u/data-go-mcp-servers@v0.12.0#subdirectory=src/nts-business-verification" data-go-mcp.nts-business-verification
   ```
   (키 없이 실행하면 경고 후 stdin 을 기다린다 — Ctrl+C.) 가능하면 Claude Desktop 에 등록해 툴 호출 1회.
7. MCPB 번들과 Smithery (통합 서버의 툴이나 키 항목이 바뀌었거나 새 태그를 태우려면):
   ```bash
   # mcpb/manifest.json 의 version, mcpb/pyproject.toml 의 version 과 tag 를 새 태그로
   uv run python scripts/gen_mcpb_manifest.py --pack   # manifest 의 tools 갱신 + dist/data-go-mcp.mcpb (Smithery 용), dist/data-go-mcp-desktop.mcpb (Claude Desktop 드래그 설치용)
   npm install -g smithery@latest && smithery auth login
   smithery mcp publish ./dist/data-go-mcp.mcpb -n hichang4u/data-go-mcp
   gh release upload vX.Y.Z dist/data-go-mcp-desktop.mcpb dist/data-go-mcp.mcpb --clobber   # 새 태그의 릴리스에. 사용자 문서는 releases/latest/download/data-go-mcp-desktop.mcpb 를 가리키므로 이 릴리스가 Latest 여야 한다
   ```
   태그가 push 된 뒤에 pack 해야 번들이 동작한다 (`tag = "vX.Y.Z"` 를 uv 가 받는다).
   `npx @anthropic-ai/mcpb validate/pack` 은 쓰지 않는다 — Smithery 는 `tools[].inputSchema` 를 요구하고 MCPB 스키마는 그 키를 거부한다(Claude Desktop 직접 설치 시 "확장 프로그램 미리보기 실패"). 그래서 Desktop 용은 `inputSchema` 를 빼고 `server.type` 을 `uv` 로 바꾼 별도 번들이다 (`python` 타입이면 Claude Desktop 이 PATH 의 `uv` 를 찾다 `spawn uv ENOENT`; `uv` 타입은 호스트가 자체 uv 로 설치한다). Claude Desktop 에서 기존 확장을 지우고 `-desktop.mcpb` 를 드래그하면 새 태그로 `.venv` 를 다시 만든다.

## README 데모 이미지

`docs/images/demo-due-diligence.png` 은 실제 실행 출력을 그린 것이다. 데모가 바뀌면 다시 만든다 (브라우저 없이 돌아간다):

```bash
uv run python scripts/demo_due_diligence.py > demo.txt
uv run --with pillow python scripts/render_demo_image.py demo.txt docs/images/demo-due-diligence.png

uv run python scripts/demo_realestate.py > realestate.txt
uv run --with pillow python scripts/render_demo_image.py realestate.txt docs/images/demo-realestate.png   --command "uv run python scripts/demo_realestate.py 강남구 202608"

uv run python scripts/demo_jobs.py > jobs.txt
uv run --with pillow python scripts/render_demo_image.py jobs.txt docs/images/demo-jobs.png   --command "uv run python scripts/demo_jobs.py 503-81-69211"

uv run python scripts/demo_bid_winners.py --business-type 용역 > bids.txt
uv run --with pillow python scripts/render_demo_image.py bids.txt docs/images/demo-bid-winners.png   --command "uv run python scripts/demo_bid_winners.py 111-81-26895 --business-type 용역"
```

Pillow 는 프로젝트 의존성이 아니라 `--with` 로만 끌어 쓴다. 한글 고정폭은 굴림체(`gulim.ttc`)를 쓴다.

## 문서 갱신 체크

- `scripts/gen_tool_docs.py --check` 가 통과하는지 (툴 시그니처가 바뀌면 가이드가 어긋난다)
- `README.md` 서버 표, `docs/guide/*` 에 새 서버/바뀐 제약 반영
