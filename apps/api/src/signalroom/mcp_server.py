import os

import httpx
from mcp.server.fastmcp import FastMCP


API = os.getenv("SIGNALROOM_API_URL", "http://127.0.0.1:8000")
mcp = FastMCP("SignalRoom")


@mcp.tool()
def search_solutioning_knowledge(query: str, limit: int = 4) -> list[dict]:
    """Search approved solutioning reference material and return evidence passages."""
    with httpx.Client(timeout=20) as client:
        response = client.get(f"{API}/api/knowledge/search", params={"query": query, "limit": limit})
        response.raise_for_status()
        return response.json()


@mcp.tool()
def get_solution_room(session_id: str) -> dict:
    """Read one persisted solution room. This tool cannot approve or modify it."""
    with httpx.Client(timeout=20) as client:
        response = client.get(f"{API}/api/sessions/{session_id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
def get_solution_evaluation(session_id: str) -> dict:
    """Return grounding and reliability metrics for one solution room."""
    with httpx.Client(timeout=20) as client:
        response = client.get(f"{API}/api/sessions/{session_id}/evaluation")
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    mcp.run(transport="stdio")
