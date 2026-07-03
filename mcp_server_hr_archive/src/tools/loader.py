from __future__ import annotations
import importlib
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Type
from pydantic import BaseModel, ValidationError, create_model
import inspect


class ToolConfig(BaseModel):
    name: Optional[str] = None
    name_tool: Optional[str] = None
    category: Optional[str] = None
    module: str  # import path, e.g., src.tools.definitions.search_archive
    attr: str = "tool"
    description: Optional[str] = None
    enabled: bool = True
    input_schema: Optional[Dict[str, str]] = None
    inputSchema: Optional[Dict[str, Any]] = None

    @property
    def tool_name(self) -> str:
        return self.name or self.name_tool or ""


_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict,
    "array": list,
    "any": Any,
}


def _parse_field_type(type_str: str):
    # simple parser: supports JSON Schema-style strings and list[T]
    if not type_str:
        return Any
    type_str = type_str.strip()
    if type_str.startswith("list[") and type_str.endswith("]"):
        inner = type_str[5:-1]
        inner_t = _TYPE_MAP.get(inner, Any)
        return List[inner_t]  # type: ignore
    return _TYPE_MAP.get(type_str, Any)


def _build_fields_from_json_schema(schema: Dict[str, Any]) -> Dict[str, Tuple[Type[Any], Any]]:
    fields: Dict[str, Tuple[Type[Any], Any]] = {}
    if schema.get("type") != "object":
        return fields
    props = schema.get("properties", {}) or {}
    required = set(schema.get("required", []))
    for name, prop in props.items():
        prop_type = prop.get("type") if isinstance(prop, dict) else None
        if prop_type == "array":
            items = prop.get("items", {}) or {}
            item_type = items.get("type")
            fields[name] = (List[_TYPE_MAP.get(item_type, Any)], ... if name in required else None)
        else:
            fields[name] = (_TYPE_MAP.get(prop_type, Any), ... if name in required else None)
    return fields


def load_tools_from_yaml(path: str) -> List[Any]:
    p = Path(path)
    if not p.exists():
        return []
    content = yaml.safe_load(p.read_text()) or {}
    tools = []
    entries = content.get("tools") or []
    for e in entries:
        try:
            cfg = ToolConfig(**e)
        except ValidationError:
            continue
        if not cfg.enabled:
            continue
        # security: only allow importing from trusted package prefix
        allowed_prefix = "src.tools.definitions"
        if not cfg.module.startswith(allowed_prefix):
            continue
        try:
            m = importlib.import_module(cfg.module)
            tool_name = cfg.tool_name
            if not tool_name:
                continue
            # if module exports a Tool object and no schema is provided, use it directly
            if cfg.input_schema is None and cfg.inputSchema is None:
                tool_obj = getattr(m, cfg.attr, None)
                if tool_obj is not None:
                    tools.append(tool_obj)
                    continue

            # Decide schema source
            model_fields: Dict[str, Tuple[Type[Any], Any]] = {}
            if cfg.input_schema:
                for fname, ftype in cfg.input_schema.items():
                    model_fields[fname] = (_parse_field_type(ftype), ...)
            elif cfg.inputSchema:
                model_fields = _build_fields_from_json_schema(cfg.inputSchema)

            if model_fields:
                Model = create_model(f"{tool_name}_Input", **model_fields)  # type: ignore
            else:
                Model = None

            # handler can be an attribute (cfg.attr) or default _impl
            handler = getattr(m, cfg.attr, None) or getattr(m, "_impl", None)
            if handler is None:
                continue

            # create wrapper that validates input and calls handler
            async def _async_wrapper(params):
                data = params or {}
                if Model is not None:
                    try:
                        parsed = Model.parse_obj(data)
                        data = parsed.model_dump() if hasattr(parsed, 'model_dump') else parsed.dict()
                    except ValidationError as ve:
                        raise ve
                # call handler (may be async or sync)
                if inspect.iscoroutinefunction(handler):
                    return await handler(data)
                else:
                    return handler(data)

            def _sync_wrapper(params):
                data = params or {}
                if Model is not None:
                    try:
                        parsed = Model.parse_obj(data)
                        data = parsed.model_dump() if hasattr(parsed, 'model_dump') else parsed.dict()
                    except ValidationError as ve:
                        raise ve
                return handler(data)

            # choose wrapper according to handler type
            wrapper = _async_wrapper if inspect.iscoroutinefunction(handler) else _sync_wrapper

            # Build a dynamic Tool object at registration time in manager
            # We'll return a tuple so manager can construct the Tool with name/desc
            tools.append((tool_name, cfg.description or getattr(m, '__doc__', ''), wrapper))
        except Exception:
            continue
    return tools
