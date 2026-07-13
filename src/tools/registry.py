from collections.abc import Callable

_TOOLS: dict[str, Callable] = {}
_MCP_TOOLS: dict[str, Callable] = {}


def register_base_tool(name: str, func: Callable) -> None:
    _TOOLS[name] = func


def register_mcp_tool(server_name: str, name: str, func: Callable) -> None:
    _MCP_TOOLS[f"{server_name}_{name}"] = func


def get_tools() -> list[Callable]:
    return list(_TOOLS.values()) + list(_MCP_TOOLS.values())


def get_tools_by_name() -> dict[str, Callable]:
    return {**_TOOLS, **_MCP_TOOLS}
