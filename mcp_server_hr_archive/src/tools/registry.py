from __future__ import annotations
from mcp.server.fastmcp import FastMCP

from tools.definitions.search_archive import search_archive
from tools.definitions.get_archive_detail import get_archive_detail
from tools.definitions.search_staff_profile import search_staff_profile
from tools.definitions.get_archive_file import get_archive_file_info


def register_all_tools(mcp: FastMCP) -> None:
    mcp.add_tool(search_archive, name="search_archive")
    mcp.add_tool(get_archive_detail, name="get_archive_detail")
    mcp.add_tool(search_staff_profile, name="search_staff_profile")
    mcp.add_tool(get_archive_file_info, name="get_archive_file_info")