from __future__ import annotations
from mcp import MCP, Tool


def register_tool(mcp: MCP, tool: Tool) -> None:
    mcp.register_tool(tool)
