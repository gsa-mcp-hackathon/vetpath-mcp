"""MCP server entry point.

The server uses stdio for local MCP clients and stateless HTTP when
running as a Databricks App or another platform that injects a port.
"""

from __future__ import annotations

import os
from urllib.parse import urlsplit

import uvicorn
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

from vetpath_mcp.config import settings
from vetpath_mcp.prompts import register_prompts
from vetpath_mcp.resources import register_resources
from vetpath_mcp.routes import register_routes
from vetpath_mcp.tools import register_tools

mcp = FastMCP(
    name="VetPath MCP",
    instructions=(
        "A source-grounded Veteran transition resource navigator. "
        "Use its tools to resolve military and VA terminology, search "
        "reviewed federal resources, retrieve program details, and return "
        "transition milestones with provenance. VetPath does not determine "
        "individual eligibility or provide clinical, legal, or financial "
        "advice."
    ),
)

register_tools(mcp)
register_prompts(mcp)
register_resources(mcp)
register_routes(mcp)


def _normalize_origin(value: str) -> str | None:
    """Normalize a URL-like value to a browser origin."""
    candidate = value.strip().rstrip("/")

    if not candidate:
        return None

    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlsplit(candidate)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    return f"{parsed.scheme}://{parsed.netloc}"


def databricks_cors_origins() -> list[str]:
    """Return exact trusted origins for browser-based MCP clients."""
    candidates = [os.getenv("DATABRICKS_HOST", "")]

    extra_origins = os.getenv(
        "VETPATH_CORS_ALLOWED_ORIGINS",
        "",
    )
    candidates.extend(extra_origins.split(","))

    origins: list[str] = []

    for candidate in candidates:
        origin = _normalize_origin(candidate)

        if origin and origin not in origins:
            origins.append(origin)

    return origins


def build_http_app() -> ASGIApp:
    """Create the stateless HTTP App with narrow CORS authorization."""
    allowed_origins = databricks_cors_origins()
    middleware: list[Middleware] = []

    if allowed_origins:
        middleware.append(
            Middleware(
                CORSMiddleware,
                allow_origins=allowed_origins,
                allow_credentials=True,
                allow_methods=[
                    "GET",
                    "POST",
                    "DELETE",
                    "OPTIONS",
                ],
                allow_headers=["*"],
                expose_headers=["Mcp-Session-Id"],
                max_age=600,
            )
        )

    return mcp.http_app(
        path="/mcp",
        stateless_http=True,
        middleware=middleware,
    )


def main() -> None:
    """Start VetPath using the transport appropriate to the environment."""
    platform_port = os.getenv("DATABRICKS_APP_PORT") or os.getenv("PORT")

    if platform_port:
        uvicorn.run(
            build_http_app(),
            host="0.0.0.0",
            port=int(platform_port),
        )
    elif settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
