"""Register the tools exposed by VetPath MCP."""

from __future__ import annotations

from vetpath_mcp.tools import (
    get_program_details,
    get_transition_milestones,
    resolve_military_terminology,
    search_veteran_resources,
)


def register_tools(mcp) -> None:
    """Register all VetPath tools with the MCP server."""
    search_veteran_resources.register(mcp)
    get_program_details.register(mcp)
    get_transition_milestones.register(mcp)
    resolve_military_terminology.register(mcp)


__all__ = ["register_tools"]
