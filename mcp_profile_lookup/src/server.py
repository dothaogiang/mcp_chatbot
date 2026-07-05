"""
Entry point MCP server. Chạy: python src/server.py
"""
import asyncio
import os
import sys

# rag/ nằm ở project root (ngang hàng với src/), thêm root vào sys.path
# để feature_manager.py import được `rag.retrieval_factory`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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