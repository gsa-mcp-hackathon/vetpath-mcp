"""Register optional MCP resources exposed by VetPath."""

from __future__ import annotations


def register_resources(mcp) -> None:
    """Register VetPath MCP resources.

    The current MVP exposes reviewed data through typed tools rather
    than directly addressable MCP resources.
    """
    _ = mcp


__all__ = ["register_resources"]
