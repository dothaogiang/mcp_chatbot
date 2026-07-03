from __future__ import annotations
from mcp import MCP, Tool
from .registry import register_tool
from pathlib import Path
from .loader import load_tools_from_yaml


TOOLS_YAML = str(Path(__file__).parents[1].joinpath("..", "Resources", "tools.yaml"))


class ToolManager:
    def __init__(self) -> None:
        self.tools = []

    def register_all(self, mcp: MCP) -> None:
        tools = load_tools_from_yaml(TOOLS_YAML)
        if not tools:
            raise RuntimeError(f"No tools loaded from YAML manifest: {TOOLS_YAML}")

        from mcp import Tool
        for t in tools:
            if isinstance(t, tuple):
                name, desc, wrapper = t
                tool_obj = Tool(name=name, description=desc or "", func=wrapper)
                register_tool(mcp, tool_obj)
            else:
                register_tool(mcp, t)
