"""Read-only MCP surface over the running API.

Three tools: search the pattern library, read a room, read the latest
evaluation results. Nothing here can create, change or approve a room; the
gate stays a human action in the product UI.
"""

import os

import httpx
from mcp.server.fastmcp import FastMCP

API = os.getenv("SIGNALROOM_API_URL", "http://127.0.0.1:8000")
mcp = FastMCP("SignalRoom")


def _get(path: str, **params) -> dict | list:
    with httpx.Client(timeout=20) as client:
        response = client.get(f"{API}{path}", params=params or None)
        response.raise_for_status()
        return response.json()


@mcp.tool()
def search_solutioning_knowledge(query: str, limit: int = 4) -> list[dict]:
    """Search the synthetic solutioning pattern library and return passages with stable ids."""
    return _get("/api/knowledge/search", query=query, limit=limit)


@mcp.tool()
def list_solution_rooms() -> list[dict]:
    """List rooms with their status, open item count and critic verdict."""
    return _get("/api/rooms")


@mcp.tool()
def get_solution_room(room_id: str) -> dict:
    """Read one room: utterances, grounded requirements, brief, critique, grounding report and metrics. Read-only."""
    return _get(f"/api/rooms/{room_id}")


@mcp.tool()
def get_latest_evaluation() -> dict:
    """Return the most recent evaluation suite results, including per-fixture failures."""
    return _get("/api/evaluation/latest")


if __name__ == "__main__":
    mcp.run(transport="stdio")
