import os
import sqlite3
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph


class SolutionState(TypedDict, total=False):
    transcript: str
    requirements: list[dict]
    retrieved_evidence: list[dict]
    architecture: list[str]
    risks: list[dict]
    ready_for_review: bool


def discover(state: SolutionState) -> SolutionState:
    return {**state, "requirements": state.get("requirements", [])}


def retrieve(state: SolutionState) -> SolutionState:
    return {**state, "retrieved_evidence": state.get("retrieved_evidence", [])}


def design(state: SolutionState) -> SolutionState:
    return {**state, "architecture": state.get("architecture", [])}


def critique(state: SolutionState) -> SolutionState:
    unsupported = [r for r in state.get("requirements", []) if not r.get("evidence")]
    return {**state, "risks": state.get("risks", []), "ready_for_review": not unsupported}


def build_graph():
    graph = StateGraph(SolutionState)
    graph.add_node("discover", discover)
    graph.add_node("retrieve", retrieve)
    graph.add_node("design", design)
    graph.add_node("critique", critique)
    graph.add_edge(START, "discover")
    graph.add_edge("discover", "retrieve")
    graph.add_edge("retrieve", "design")
    graph.add_edge("design", "critique")
    graph.add_edge("critique", END)
    data_dir = Path(os.getenv("SIGNALROOM_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(data_dir / "langgraph.sqlite3", check_same_thread=False)
    return graph.compile(checkpointer=SqliteSaver(connection))


solution_graph = build_graph()


def run_solution_graph(state: SolutionState, thread_id: str) -> SolutionState:
    return solution_graph.invoke(state, config={"configurable": {"thread_id": thread_id}})


def graph_history(thread_id: str) -> list[dict]:
    config = {"configurable": {"thread_id": thread_id}}
    return [
        {
            "step": snapshot.metadata.get("step"),
            "source": snapshot.metadata.get("source"),
            "next": list(snapshot.next),
            "created_at": snapshot.created_at,
        }
        for snapshot in solution_graph.get_state_history(config)
    ]
