"""Entry point for MCP Server — exposes tools via streamable-http.
"""
import asyncio
from mcp import FastMCP

from config.settings import Settings
from tools.manager import ToolManager
from logger import setup_logging
from app_context import init_app


def create_app() -> FastMCP:
    settings = Settings()
    setup_logging(settings)

    # initialize app singletons
    init_app(settings)

    mcp = FastMCP(name="mcp-server-hr-archive")

    # Register tools
    manager = ToolManager()
    manager.register_all(mcp)

    return mcp


def main() -> None:
    mcp = create_app()
    # run streamable-http adapter (the SDK provides streamable-http integration)
    mcp.run(streamable_http=True)


if __name__ == "__main__":
    main()
