"""Custom HTTP routes for VetPath MCP.

These routes are active when the server uses HTTP transport. They sit
alongside the Streamable HTTP MCP endpoint at ``/mcp``.
"""

from __future__ import annotations

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from vetpath_mcp import __version__


def health_payload() -> dict[str, str]:
    """Return the stable health response used by deployment checks."""
    return {
        "status": "healthy",
        "service": "vetpath-mcp",
        "version": __version__,
    }


def register_routes(mcp: FastMCP) -> None:
    """Register custom HTTP routes with the server."""

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        _ = request
        return JSONResponse(health_payload())

    @mcp.custom_route("/version", methods=["GET"])
    async def version(request: Request) -> JSONResponse:
        _ = request
        return JSONResponse({"version": __version__})
