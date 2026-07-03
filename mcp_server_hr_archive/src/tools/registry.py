from __future__ import annotations
import importlib
from pathlib import Path
from typing import Any, Dict, List

import yaml
from mcp.server.fastmcp import FastMCP

from logger import get_logger

log = get_logger(__name__)

# File này ở src/tools/registry.py -> lên 2 cấp là gốc mcp_server_hr_archive/
TOOLS_YAML = Path(__file__).resolve().parents[2] / "Resources" / "tools.yaml"

# Chỉ cho phép import module nằm trong package tool definitions -> tránh
# yaml bị chỉnh sửa (vô tình hoặc cố ý) để import bừa module ngoài ý muốn.
ALLOWED_MODULE_PREFIX = "tools.definitions"


def _load_tool_entries() -> List[Dict[str, Any]]:
    if not TOOLS_YAML.exists():
        raise FileNotFoundError(f"Không tìm thấy tool manifest: {TOOLS_YAML}")
    content = yaml.safe_load(TOOLS_YAML.read_text(encoding="utf-8")) or {}
    return content.get("tools", []) or []


def register_all_tools(mcp: FastMCP) -> None:
    entries = _load_tool_entries()
    if not entries:
        raise RuntimeError(f"tools.yaml rỗng hoặc không có key 'tools': {TOOLS_YAML}")

    registered = 0
    for entry in entries:
        name_tool = entry.get("name_tool")
        module_path = entry.get("module")
        attr = entry.get("attr") or name_tool
        enabled = entry.get("enabled", True)
        description = entry.get("description")

        if not enabled:
            log.info("Bỏ qua tool bị tắt (enabled: false): %s", name_tool)
            continue
        if not name_tool or not module_path:
            log.warning("Entry thiếu name_tool/module trong tools.yaml, bỏ qua: %s", entry)
            continue
        if not module_path.startswith(ALLOWED_MODULE_PREFIX):
            log.error(
                "Từ chối đăng ký '%s': module '%s' không nằm trong prefix cho phép '%s'",
                name_tool, module_path, ALLOWED_MODULE_PREFIX,
            )
            continue

        try:
            module = importlib.import_module(module_path)
        except ImportError:
            log.exception("Không import được module '%s' cho tool '%s'", module_path, name_tool)
            continue

        fn = getattr(module, attr, None)
        if fn is None or not callable(fn):
            log.error("Module '%s' không có hàm '%s' cho tool '%s'", module_path, attr, name_tool)
            continue

        mcp.add_tool(
            fn,
            name=name_tool,
            description=description or (fn.__doc__ or "").strip() or None,
        )
        log.info("Đã đăng ký tool: %s", name_tool)
        registered += 1

    if registered == 0:
        raise RuntimeError("Không đăng ký được tool nào từ tools.yaml — kiểm tra lại manifest.")

    log.info("Đăng ký thành công %d/%d tool từ %s", registered, len(entries), TOOLS_YAML)