"""Register optional reusable VetPath prompts."""

from __future__ import annotations


def register_prompts(mcp) -> None:
    """Register VetPath prompts.

    The current MVP does not expose server-managed prompts.
    """
    _ = mcp


__all__ = ["register_prompts"]
