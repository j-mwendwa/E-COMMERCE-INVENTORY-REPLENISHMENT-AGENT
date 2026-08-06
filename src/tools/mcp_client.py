"""
MCP Client — connects to MCP servers from the Anthropic registry and
registers their tools so the LLM agent can use them.

Supports both stdio (npx) and SSE transports.
Env var references like ${DATABASE_URL} are resolved from settings.
"""

import os
import re

import structlog
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client

from src.config import cfg, settings
from src.tools.registry import register_mcp_tool

log = structlog.get_logger()


def _resolve_env(value: str) -> str:
    """Replace ${VAR} placeholders with values from settings or os.environ."""

    def _replace(m: re.Match) -> str:
        name = m.group(1)
        return str(getattr(settings, name.lower(), os.environ.get(name, "")))

    return re.sub(r"\$\{(\w+)\}", _replace, value)


async def load_mcp_tools() -> int:
    mcp_cfg = cfg.get("mcp", {})
    if not mcp_cfg.get("enabled", False):
        log.info("mcp_disabled")
        return 0

    servers = mcp_cfg.get("servers", {})
    if not servers:
        log.info("mcp_no_servers_configured")
        return 0

    total = 0
    for name, server_cfg in servers.items():
        try:
            count = await _load_server(name, server_cfg)
            total += count
        except Exception:
            log.exception("mcp_server_load_failed", server=name)

    log.info("mcp_tools_loaded", total=total)
    return total


async def _load_server(name: str, server_cfg: dict) -> int:
    transport = server_cfg.get("transport", "stdio")
    if transport == "sse":
        return await _load_sse(name, server_cfg)
    return await _load_stdio(name, server_cfg)


async def _load_sse(name: str, server_cfg: dict) -> int:
    url = _resolve_env(server_cfg["url"])
    log.info("mcp_connect_sse", server=name, url=url)
    async with sse_client(url=url) as streams, ClientSession(streams[0], streams[1]) as session:
        await session.initialize()
        tools = (await session.list_tools()).tools
        for t in tools:
            register_mcp_tool(name, t.name, _wrap_tool(session, t.name))
        return len(tools)


async def _load_stdio(name: str, server_cfg: dict) -> int:
    cmd = server_cfg["command"]
    args = [_resolve_env(a) for a in server_cfg.get("args", [])]
    env_dict = {k: _resolve_env(v) for k, v in server_cfg.get("env", {}).items()}
    merged = {**os.environ, **env_dict} if env_dict else None

    params = StdioServerParameters(command=cmd, args=args, env=merged)
    log.info("mcp_connect_stdio", server=name, command=cmd)
    async with stdio_client(params) as streams, ClientSession(streams[0], streams[1]) as session:
        await session.initialize()
        tools = (await session.list_tools()).tools
        for t in tools:
            register_mcp_tool(name, t.name, _wrap_tool(session, t.name))
        return len(tools)


def _wrap_tool(session: ClientSession, tool_name: str):
    async def fn(**kwargs) -> str:
        result = await session.call_tool(tool_name, kwargs)
        return str(result.content[0].text) if result.content else ""

    fn.__name__ = tool_name
    fn.__doc__ = f"MCP tool: {tool_name}"
    return fn
