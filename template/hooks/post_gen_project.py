#!/usr/bin/env python
"""Post-generation hook for setting up the new MCP server project."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


# Windows 콘솔(cp949)에서 이모지 출력이 죽지 않도록
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]


def run_command(cmd, cwd=None):
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        print(f"✓ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {cmd}")
        print(f"  Error: {e.stderr}")
        return False


def main():
    """Post-generation setup."""
    project_dir = Path.cwd()
    
    print("\n🚀 Setting up your new MCP server...")
    
    # 모노레포(uv workspace)의 src/ 아래에 생성되므로 git init 은 하지 않는다 (중첩 저장소 방지).
    # 의존성은 워크스페이스 루트에서 설치한다.
    root = project_dir.parent.parent
    uv = shutil.which("uv")
    if uv is None:
        print("  uv not found on PATH - run 'uv sync --dev --all-packages' and the tests manually.")
    elif run_command(f'"{uv}" sync --dev --all-packages', cwd=root):
        print("  Installed workspace dependencies")
    else:
        print("  Failed to install dependencies. Run 'uv sync --dev --all-packages' at the repo root.")

    if uv is not None and run_command(f'"{uv}" run pytest src/{project_dir.name}/tests -q', cwd=root):
        print("  Template tests passed!")
    elif uv is not None:
        print("  Template tests failed - check the output above.")

    # 4. Print next steps
    print("\n✨ Your MCP server '{{ cookiecutter.api_name }}' is ready!")
    print("\n📝 Next steps:")
    print("  1. Update api_client.py with your API endpoints")
    print("  2. Define data models in models.py")
    print("  3. Implement MCP tools in server.py")
    print("  4. Update tests to match your implementation")
    print("  5. Update README.md with your tool documentation")
    print("\n🔑 Don't forget to set your API key:")
    print(f"  export {{ cookiecutter.api_key_env_name }}='your-api-key'")
    print("\n🏃 To run your server:")
    print("  uv run python -m data_go_mcp.{{ cookiecutter.api_name_underscore }}.server")
    print("\n📦 To build for PyPI:")
    print("  uv build")
    print("\n💡 For more information, see CONTRIBUTING.md in the main repository.")


if __name__ == "__main__":
    main()