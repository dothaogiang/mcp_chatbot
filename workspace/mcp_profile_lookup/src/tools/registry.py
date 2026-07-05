"""
ToolRegistry: match tool_name (trong tools.yaml) với hàm cùng tên trong
ProfileFeatureManager, build Tool object cho FastMCP.

Thêm tool mới chỉ cần:
  1. Thêm entry trong Resources/tools.yaml
  2. Viết 1 method cùng tên trong ProfileFeatureManager (feature_manager.py)
Không cần sửa registry.py hay server.py.
"""
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools.base import Tool
from mcp.server.fastmcp.utilities.func_metadata import func_metadata

from tools.manager import CustomToolManager
from feature_manager import ProfileFeatureManager
from config.configs import config_object
from logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    def __init__(self, name: str):
        self.name = name
        self.tool_manager = CustomToolManager()
        self.list_tool = []

    async def register_tools(self, category: str = "mcp") -> FastMCP:
        tools_to_register = self.tool_manager.get_tools_by_category(category)

        if not tools_to_register:
            logger.warning(f"Không có tool nào trong category '{category}'")

        for tool_name, tool_definition in tools_to_register.items():
            fn = getattr(ProfileFeatureManager, tool_name, None)
            if fn is None:
                logger.error(
                    f"Tool '{tool_name}' khai báo trong tools.yaml nhưng KHÔNG "
                    f"tìm thấy hàm cùng tên trong ProfileFeatureManager -> bỏ qua."
                )
                continue

            fn_metadata = func_metadata(fn, skip_names=[])

            tool = Tool(
                fn=fn,
                title=tool_name,
                name=tool_name,
                description=tool_definition["description"],
                parameters=tool_definition["inputSchema"],
                is_async=True,
                fn_metadata=fn_metadata,
                context_kwarg=None,
                annotations=None,
            )
            self.list_tool.append(tool)
            logger.info(f"Đã đăng ký tool: {tool_name}")

        server_mcp = FastMCP(
            name=self.name,
            tools=self.list_tool,
            host=config_object.URL_HOST_SERVER,
            port=config_object.PORT_SERVER,
        )
        return server_mcp
