"""Optional MCP server exposing useful iae tools to agents.

Run: `python -m i_am_an_engineer.mcp_server` (requires optional `mcp` extra).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_iae(args: list[str]) -> str:
    cmd = [sys.executable, "-m", "i_am_an_engineer", *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    body = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        return f"exit {r.returncode}\n{body}"
    return body or "(ok)"


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            "iae MCP server needs the optional dependency: pip install 'i-am-an-engineer[mcp]'",
            file=sys.stderr,
        )
        raise SystemExit(1)

    mcp = FastMCP("i-am-an-engineer")

    @mcp.tool()
    def iae_doctor() -> str:
        """Check ffmpeg, keys, and project health."""
        return _run_iae(["doctor", "--json"])

    @mcp.tool()
    def iae_record_guide() -> str:
        """Print the 30–60 minute English recording session shot list."""
        return _run_iae(["record", "guide", "--builtin"])

    @mcp.tool()
    def iae_publish_check(project: str = ".") -> str:
        """Run publish consistency / safety checks on a project."""
        return _run_iae(["publish", "check", "--project", project])

    @mcp.tool()
    def iae_pipeline_plan(project: str = ".") -> str:
        """Return the planned pipeline stages for a project."""
        return _run_iae(["run", "--plan-only", "--project", project])

    @mcp.tool()
    def iae_kb_search(query: str) -> str:
        """Search the knowledge base."""
        return _run_iae(["kb", "search", query])

    mcp.run()


if __name__ == "__main__":
    main()
