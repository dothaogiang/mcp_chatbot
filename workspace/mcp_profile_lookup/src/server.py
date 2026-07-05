"""
Entry point MCP server. Chạy: python server.py (từ trong thư mục src/)
"""
import asyncio
from tools.registry import ToolRegistry
from logger import get_logger

logger = get_logger(__name__)

mcp = ToolRegistry(name="profile_lookup")


async def main():
    server_mcp = await mcp.register_tools(category="mcp")
    return server_mcp


if __name__ == "__main__":
    server_mcp = asyncio.run(main())
    logger.info("Server sẵn sàng, bắt đầu lắng nghe...")
    server_mcp.run(transport="streamable-http")
