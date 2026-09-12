# 릴리스

## 배포 경로

**git 직접 설치**가 기본이다. 사용자는 `uvx --from "git+…#subdirectory=src/<server>" data-go-mcp.<server>` 로 실행하며, uv 가 저장소를 받아 워크스페이스(`[tool.uv.sources] data-go-mcp-core = { workspace = true }`)를 그대로 해석하므로 core 를 따로 배포할 필요가 없다 (2026-09-12 확인).

PyPI 는 쓰지 않는다. 원저장소의 `data-go-mcp.*` 네임스페이스는 우리 것이 아니고, git 설치로 충분하다. 필요해지면 `scripts/deploy_to_pypi.py` (core 를 먼저 올리도록 정렬돼 있음)와 새 네임스페이스를 정한다.

## 버전

- 각 `src/*/pyproject.toml` 의 `version`. 서버는 각자 올린다 — 툴이 바뀐 서버만 bump (v0.4.0 시점: nps·fsc 0.5.0, 나머지 0.3.0), core 는 독립 (0.1.x).
- fsc 의 `SERVER_VERSION` 은 패키지 메타데이터에서 읽으므로 손댈 곳이 없다.
- git 태그 `vX.Y.Z` 는 저장소 전체 스냅샷이며 서버 버전과 무관하게 올라간다. 사용자는 `data-go-mcp-servers@v0.4.0#subdirectory=…` 로 고정할 수 있다.

## 절차

1. `main` 이 green 인지 확인 (CI).
2. `src/*/CHANGELOG.md` 에 항목 추가. 형식은 Keep a Changelog.
3. 버전 bump: `src/*/pyproject.toml` (+ `src/*/data_go_mcp/*/__init__.py` 의 `__version__` 이 있으면 함께).
4. `uv lock` 후 커밋: `chore(release): v0.4.0`.
5. 태그와 릴리스:
   ```bash
   git tag -a v0.4.0 -m "v0.4.0"
   git push origin main --tags
   gh release create v0.4.0 --title "v0.4.0" --notes-file <notes>
   ```
6. 새 환경에서 확인:
   ```bash
   uvx --refresh --from "git+https://github.com/hichang4u/data-go-mcp-servers@v0.4.0#subdirectory=src/nts-business-verification" data-go-mcp.nts-business-verification
   ```
   (키 없이 실행하면 경고 후 stdin 을 기다린다 — Ctrl+C.) 가능하면 Claude Desktop 에 등록해 툴 호출 1회.

## 문서 갱신 체크

- `scripts/gen_tool_docs.py --check` 가 통과하는지 (툴 시그니처가 바뀌면 가이드가 어긋난다)
- `README.md` 서버 표, `docs/guide/*` 에 새 서버/바뀐 제약 반영
