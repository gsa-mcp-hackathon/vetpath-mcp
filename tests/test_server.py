"""Smoke and deployment tests for the VetPath MCP server."""

from __future__ import annotations

import pytest
from fastmcp import FastMCP
from starlette.testclient import TestClient

import vetpath_mcp.app as app_module
from vetpath_mcp.app import (
    build_http_app,
    databricks_cors_origins,
    mcp,
)
from vetpath_mcp.config import settings

EXPECTED_TOOL_NAMES = {
    "get_program_details",
    "get_transition_milestones",
    "resolve_military_terminology",
    "search_veteran_resources",
}


def test_server_is_importable():
    assert mcp is not None


def test_server_has_name():
    assert mcp.name == "VetPath MCP"


def test_default_transport_is_stdio():
    """Guard against accidentally changing the local default."""
    assert settings.mcp_transport == "stdio"


def test_tools_register_without_error():
    from vetpath_mcp.tools import register_tools

    register_tools(FastMCP("test"))


def test_prompts_register_without_error():
    from vetpath_mcp.prompts import register_prompts

    register_prompts(FastMCP("test"))


def test_resources_register_without_error():
    from vetpath_mcp.resources import register_resources

    register_resources(FastMCP("test"))


def test_routes_register_without_error():
    from vetpath_mcp.routes import register_routes

    register_routes(FastMCP("test"))


@pytest.mark.asyncio
async def test_only_vetpath_tools_are_discoverable():
    """The production server exposes only reviewed VetPath tools."""
    tools = await mcp.list_tools()
    tool_names = {tool.name for tool in tools}

    assert tool_names == EXPECTED_TOOL_NAMES


def test_health_payload_uses_vetpath_identity():
    from vetpath_mcp.routes import health_payload

    payload = health_payload()

    assert payload["status"] == "healthy"
    assert payload["service"] == "vetpath-mcp"
    assert payload["version"]


def test_cors_origin_is_derived_from_workspace_host(monkeypatch):
    origin = "https://dbc-aae0ba16-8727.cloud.databricks.com"

    monkeypatch.setenv(
        "DATABRICKS_HOST",
        f"{origin}/",
    )
    monkeypatch.delenv(
        "VETPATH_CORS_ALLOWED_ORIGINS",
        raising=False,
    )

    assert databricks_cors_origins() == [origin]


def test_genie_code_cors_preflight_is_allowed(monkeypatch):
    origin = "https://dbc-aae0ba16-8727.cloud.databricks.com"

    monkeypatch.setenv("DATABRICKS_HOST", origin)
    monkeypatch.delenv(
        "VETPATH_CORS_ALLOWED_ORIGINS",
        raising=False,
    )

    app = build_http_app()

    with TestClient(app) as client:
        response = client.options(
            "/mcp",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": (
                    "authorization,content-type,mcp-protocol-version,mcp-session-id"
                ),
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


def test_untrusted_cors_origin_is_rejected(monkeypatch):
    workspace_origin = "https://dbc-aae0ba16-8727.cloud.databricks.com"

    monkeypatch.setenv(
        "DATABRICKS_HOST",
        workspace_origin,
    )
    monkeypatch.delenv(
        "VETPATH_CORS_ALLOWED_ORIGINS",
        raising=False,
    )

    app = build_http_app()

    with TestClient(app) as client:
        response = client.options(
            "/mcp",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_databricks_runtime_uses_cors_http_app(monkeypatch):
    captured: dict[str, object] = {}
    sentinel_app = object()

    def fake_run(app, **kwargs):
        captured["app"] = app
        captured.update(kwargs)

    monkeypatch.setenv("DATABRICKS_APP_PORT", "8123")
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.setattr(
        app_module,
        "build_http_app",
        lambda: sentinel_app,
    )
    monkeypatch.setattr(
        app_module.uvicorn,
        "run",
        fake_run,
    )

    app_module.main()

    assert captured == {
        "app": sentinel_app,
        "host": "0.0.0.0",
        "port": 8123,
    }
