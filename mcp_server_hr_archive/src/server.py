from __future__ import annotations
from mcp.server.fastmcp import FastMCP

from config.settings import get_settings
from logger import setup_logging, get_logger
from app_context import init_app, close_app
from tools.registry import register_all_tools

log = get_logger(__name__)


def create_app() -> FastMCP:
    settings = get_settings()
    setup_logging(settings)
    init_app(settings)

    mcp = FastMCP("mcp-server-hr-archive")
    register_all_tools(mcp)
    return mcp


def main() -> None:
    mcp = create_app()
    try:
        mcp.run(transport="streamable-http")
    finally:
        close_app()


if __name__ == "__main__":
    main()