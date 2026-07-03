from __future__ import annotations
from mcp.server.fastmcp import FastMCP

from app_context import lifespan
from tools.registry import register_all_tools


def create_app() -> FastMCP:
    mcp = FastMCP("mcp-server-hr-archive", lifespan=lifespan, port=8010)
    register_all_tools(mcp)
    return mcp


def main() -> None:
    mcp = create_app()
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()