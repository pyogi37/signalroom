"""The solution graph.

    START -> discover -> extract -> retrieve -> design -> critique -> gate
                            ^                     ^                   |
                            |                     |                   +--> END (approve)
                            |                     +---- request_changes
                            +--------------------------- follow_up

Each node does its own work and records what it did. Discover and retrieve
are deterministic code. Extract, design and critique call the model through
`structured_call` and then hand the output to `grounding.py`, which decides
what survives. The gate is a LangGraph `interrupt`: the graph pauses, the
API stores the room, and a later human decision resumes the same thread.
State is checkpointed in SQLite so a room can be resumed after a restart.

State values are plain dicts (Pydantic dumps) so the checkpointer never has
to know about the domain classes.
"""

import logging
import sqlite3
from datetime import datetime, timezone
from time import perf_counter
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .config import data_dir
from .grounding import check_brief, ground_extraction, is_real_answer, similar_questions
from .model_client import ModelCallFailed, ModelUnavailable, structured_call
from .models import (
    Brief,
    BriefDraft,
    Contradiction,
    Critique,
    CritiqueDraft,
    Decision,
    Extraction,
    Finding,
    GroundingReport,
    OpenItem,
    Requirement,
    Room,
    RunMetrics,
    SearchHit,
    StageMetric,
    StageRecord,
    UseCase,
    Utterance,
)
from .prompts import CRITIQUE_SYSTEM, DESIGN_SYSTEM, EXTRACT_SYSTEM, critique_user, design_user, extract_user
from .retrieval import store
from .segmentation import segment, speakers

log = logging.getLogger("signalroom.workflow")
STAGE_ORDER = ["Discover", "Extract", "Retrieve", "Design", "Critique", "Gate"]
WAITING = "Waiting for the solution engineer"


class SolutionState(TypedDict, total=False):
    room_id: str
    organization: str
    industry: str
    transcript: str
    model_mode: str | None
    utterances: list[dict]
    speakers: list[dict]
    requirements: list[dict]
    use_cases: list[dict]
    open_items: list[dict]
    contradictions: list[dict]
    grounding: dict
    retrieved: list[dict]
    brief: dict | None
    design_findings: list[dict]
    critique: dict | None
    stages: list[dict]
    metrics: list[dict]
    status: str
    review_note: str | None
    decisions: list[dict]
    gate: str | None
    error: str | None
    error_kind: str | None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _stages(state: SolutionState, name: str, status: str, detail: str, latency_ms: float = 0.0) -> list[dict]:
    kept = [item for item in state.get("stages", []) if item["name"] != name]
    kept.append(StageRecord(name=name, status=status, detail=detail, latency_ms=round(latency_ms, 1)).model_dump())  # type: ignore[arg-type]
    return sorted(kept, key=lambda item: STAGE_ORDER.index(item["name"]))


def _metrics(state: SolutionState, call) -> list[dict]:
    metric = StageMetric(
        stage=call.stage, mode=call.mode, model=call.model, latency_ms=call.latency_ms,
        input_tokens=call.input_tokens, output_tokens=call.output_tokens, estimated_cost_usd=call.estimated_cost_usd,
    )
    return state.get("metrics", []) + [metric.model_dump()]


def _fail(state: SolutionState, stage: str, error: Exception, started: float) -> SolutionState:
    kind = "model_unavailable" if isinstance(error, ModelUnavailable) else "model_failed"
    log.warning("Room %s: stage %s failed in mode %s: %s", state.get("room_id"), stage, state.get("model_mode") or "configured", error)
    return {
        "error": str(error), "error_kind": kind, "status": "failed",
        "stages": _stages(state, stage, "failed", str(error)[:240], (perf_counter() - started) * 1000),
    }


def _ms(started: float) -> float:
    return (perf_counter() - started) * 1000


# ----------------------------------------------------------------------------
# Nodes
# ----------------------------------------------------------------------------


def discover(state: SolutionState) -> SolutionState:
    started = perf_counter()
    utterances = segment(state["transcript"])
    roster = speakers(utterances)
    return {
        "utterances": [item.model_dump() for item in utterances],
        "speakers": [item.model_dump() for item in roster],
        "status": "running", "error": None, "error_kind": None, "gate": None,
        "stages": _stages(state, "Discover", "complete", f"{len(utterances)} lines, {len(roster)} speakers", _ms(started)),
    }


def extract(state: SolutionState) -> SolutionState:
    started = perf_counter()
    utterances = [Utterance(**item) for item in state["utterances"]]
    existing = [OpenItem(**item) for item in state.get("open_items", [])]
    roster = speakers(utterances)
    try:
        extraction, call = structured_call(
            "extract", EXTRACT_SYSTEM,
            extract_user(state["organization"], state.get("industry", ""), utterances, roster, existing or None),
            Extraction, mode=state.get("model_mode"),
        )
    except (ModelUnavailable, ModelCallFailed) as error:
        return _fail(state, "Extract", error, started)
    requirements, use_cases, open_items, contradictions, report = ground_extraction(extraction, utterances, existing)
    open_count = sum(1 for item in open_items if item.status == "open")
    detail = (
        f"{len(requirements)} requirements, {len(use_cases)} use cases, {open_count} open items; "
        f"grounding {report.passed}/{report.proposed} passed"
    )
    if report.repaired:
        detail += f", {report.repaired} repaired"
    if report.dropped:
        detail += f", {report.dropped} dropped"
    return {
        "requirements": [item.model_dump() for item in requirements],
        "use_cases": [item.model_dump() for item in use_cases],
        "open_items": [item.model_dump() for item in open_items],
        "contradictions": [item.model_dump() for item in contradictions],
        "grounding": report.model_dump(),
        "metrics": _metrics(state, call),
        "stages": _stages(state, "Extract", "complete", detail, _ms(started)),
    }


def retrieve(state: SolutionState) -> SolutionState:
    started = perf_counter()
    requirements = [Requirement(**item) for item in state.get("requirements", [])]
    use_cases = [UseCase(**item) for item in state.get("use_cases", [])]
    merged: dict[str, SearchHit] = {}

    def collect(query: str, supports: str) -> None:
        for hit in store.search(query, limit=3):
            current = merged.get(hit.passage_id)
            if current is None:
                hit.supports = [supports]
                merged[hit.passage_id] = hit
            else:
                current.score = max(current.score, hit.score)
                if supports not in current.supports:
                    current.supports.append(supports)

    for item in requirements:
        collect(f"{item.title} {item.detail} {item.evidence.quote}", item.id)
    for case in use_cases:
        collect(f"{case.name} {case.trigger_condition} {case.expected_output}", case.id)
    ranked = sorted(merged.values(), key=lambda hit: hit.score, reverse=True)[:8]
    detail = f"{len(ranked)} passages from the pattern library" if ranked else "no reference passages matched"
    return {
        "retrieved": [hit.model_dump() for hit in ranked],
        "stages": _stages(state, "Retrieve", "complete", detail, _ms(started)),
    }


def design(state: SolutionState) -> SolutionState:
    started = perf_counter()
    utterances = [Utterance(**item) for item in state["utterances"]]
    requirements = [Requirement(**item) for item in state.get("requirements", [])]
    use_cases = [UseCase(**item) for item in state.get("use_cases", [])]
    open_items = [OpenItem(**item) for item in state.get("open_items", [])]
    contradictions = [Contradiction(**item) for item in state.get("contradictions", [])]
    retrieved = [SearchHit(**item) for item in state.get("retrieved", [])]
    previous = Brief(**state["brief"]) if state.get("brief") else None
    review_note = state.get("review_note") or None
    try:
        draft, call = structured_call(
            "design", DESIGN_SYSTEM,
            design_user(state["organization"], state.get("industry", ""), utterances, requirements, use_cases,
                        open_items, contradictions, retrieved, review_note, previous),
            BriefDraft, mode=state.get("model_mode"),
        )
    except (ModelUnavailable, ModelCallFailed) as error:
        return _fail(state, "Design", error, started)
    draft, findings = check_brief(draft, utterances, retrieved)

    next_index = len(open_items) + 1
    valid_lines = {item.line for item in utterances}
    for proposed in draft.additional_open_items:
        if any(similar_questions(proposed.question, existing.question) for existing in open_items):
            continue
        open_items.append(OpenItem(
            id=f"OI-{next_index:02d}", question=proposed.question, why_it_matters=proposed.why_it_matters,
            suggested_owner_role=proposed.suggested_owner_role or "Unassigned",
            related_line=proposed.related_line if proposed.related_line in valid_lines else None,
        ))
        next_index += 1

    brief = Brief(**draft.model_dump(exclude={"additional_open_items"}), revision=(previous.revision + 1) if previous else 1)
    detail = f"brief revision {brief.revision}: {len(brief.recommendation.phases)} phases, {len(brief.constraints)} constraints"
    if findings:
        detail += f", {len(findings)} code checks raised"
    return {
        "brief": brief.model_dump(),
        "design_findings": [item.model_dump() for item in findings],
        "open_items": [item.model_dump() for item in open_items],
        "review_note": None,
        "metrics": _metrics(state, call),
        "stages": _stages(state, "Design", "complete", detail, _ms(started)),
    }


def critique(state: SolutionState) -> SolutionState:
    started = perf_counter()
    utterances = [Utterance(**item) for item in state["utterances"]]
    requirements = [Requirement(**item) for item in state.get("requirements", [])]
    use_cases = [UseCase(**item) for item in state.get("use_cases", [])]
    open_items = [OpenItem(**item) for item in state.get("open_items", [])]
    contradictions = [Contradiction(**item) for item in state.get("contradictions", [])]
    brief = Brief(**state["brief"])
    try:
        draft, call = structured_call(
            "critique", CRITIQUE_SYSTEM,
            critique_user(utterances, requirements, use_cases, open_items, contradictions, brief),
            CritiqueDraft, mode=state.get("model_mode"),
        )
    except (ModelUnavailable, ModelCallFailed) as error:
        return _fail(state, "Critique", error, started)

    valid_lines = {item.line for item in utterances}
    findings = [
        Finding(kind=item.kind, severity=item.severity, text=item.text, location=item.location,
                lines=[line for line in item.lines if line in valid_lines], source="model")
        for item in draft.findings
    ]
    findings += [Finding(**item) for item in state.get("design_findings", [])]
    grounding = GroundingReport(**state.get("grounding", {}))
    for drop in grounding.drops:
        findings.append(Finding(
            kind="dropped_evidence", severity="medium", source="code", location="extraction",
            text=(f"The model proposed the {drop.kind.replace('_', ' ')} '{drop.title}' citing L{drop.proposed_line}, "
                  f"but the quote was not found there ({drop.reason.replace('_', ' ')}). It was dropped before the brief was drafted."),
            lines=[drop.proposed_line] if drop.proposed_line in valid_lines else [],
        ))
    for item in open_items:
        if item.status == "open" and item.suggested_owner_role.strip().lower() in {"", "unassigned"}:
            findings.append(Finding(kind="missing_owner", severity="low", source="code", location=item.id,
                                    text=f"{item.id} has no suggested owner role.", lines=[item.related_line] if item.related_line else []))
    model_contradiction_lines = {line for item in findings if item.kind == "contradiction" for line in item.lines}
    for item in contradictions:
        if item.line_a in model_contradiction_lines or item.line_b in model_contradiction_lines:
            continue
        findings.append(Finding(kind="contradiction", severity="medium", source="code", location="transcript",
                                text=f"{item.topic}: L{item.line_a} and L{item.line_b} disagree. {item.note}", lines=[item.line_a, item.line_b]))

    verdict = "needs_changes" if any(item.severity == "high" for item in findings) else draft.verdict
    high = sum(1 for item in findings if item.severity == "high")
    result = Critique(findings=findings, verdict=verdict, summary=draft.summary)
    detail = f"{len(findings)} findings ({high} high), {verdict.replace('_', ' ')}"
    stages = _stages(state, "Critique", "complete", detail, _ms(started))
    stages = _stages({"stages": stages}, "Gate", "active", WAITING)
    return {"critique": result.model_dump(), "metrics": _metrics(state, call), "stages": stages}


def gate(state: SolutionState) -> SolutionState:
    open_items = [OpenItem(**item) for item in state.get("open_items", [])]
    critique_state = state.get("critique") or {}
    decision = interrupt({
        "room_id": state["room_id"],
        "waiting_for": "solution engineer",
        "requirements": len(state.get("requirements", [])),
        "open_items": sum(1 for item in open_items if item.status == "open"),
        "verdict": critique_state.get("verdict"),
    })
    kind = decision.get("kind")
    record = Decision(kind=kind, note=str(decision.get("note") or ""), decided_at=_now()).model_dump()
    decisions = state.get("decisions", []) + [record]

    if kind == "approve":
        return {"status": "approved", "gate": "approve", "decisions": decisions,
                "stages": _stages(state, "Gate", "complete", "Approved by the solution engineer")}

    if kind == "request_changes":
        note = str(decision.get("note") or "Changes requested")
        return {"status": "running", "gate": "request_changes", "review_note": note, "decisions": decisions,
                "stages": _stages(state, "Gate", "pending", "Changes requested; revising the brief")}

    utterances = [Utterance(**item) for item in state["utterances"]]
    by_id = {item.id: item for item in open_items}
    speaker = str(decision.get("answered_by") or "Follow-up answer")
    next_line = (utterances[-1].line + 1) if utterances else 1
    added = rejected = 0
    for answer in decision.get("answers", []):
        item = by_id.get(str(answer.get("open_item_id")))
        text = str(answer.get("answer") or "").strip()
        if item is None or item.status == "answered" or not text:
            continue
        if not is_real_answer(text):
            item.rejected_answers.append(text)
            rejected += 1
        utterances.append(Utterance(line=next_line, speaker=speaker, text=f"Answer to {item.id} ({item.question}): {text}", origin="follow_up"))
        next_line += 1
        added += 1
    detail = f"{added} follow-up answers added; re-running extraction"
    if rejected:
        detail += f" ({rejected} did not state a fact and cannot close an item)"
    return {
        "utterances": [item.model_dump() for item in utterances],
        "speakers": [item.model_dump() for item in speakers(utterances)],
        "open_items": [item.model_dump() for item in open_items],
        "status": "running", "gate": "follow_up", "decisions": decisions,
        "stages": _stages(state, "Gate", "pending", detail),
    }


# ----------------------------------------------------------------------------
# Graph
# ----------------------------------------------------------------------------


def _continue_to(next_node: str):
    def route(state: SolutionState) -> str:
        return END if state.get("error") else next_node
    return route


def _after_gate(state: SolutionState) -> str:
    return {"approve": END, "request_changes": "design", "follow_up": "extract"}.get(state.get("gate") or "", END)


def build_graph(checkpointer=None):
    graph = StateGraph(SolutionState)
    graph.add_node("discover", discover)
    graph.add_node("extract", extract)
    graph.add_node("retrieve", retrieve)
    graph.add_node("design", design)
    graph.add_node("critique", critique)
    graph.add_node("gate", gate)
    graph.add_edge(START, "discover")
    graph.add_edge("discover", "extract")
    graph.add_conditional_edges("extract", _continue_to("retrieve"), {"retrieve": "retrieve", END: END})
    graph.add_edge("retrieve", "design")
    graph.add_conditional_edges("design", _continue_to("critique"), {"critique": "critique", END: END})
    graph.add_conditional_edges("critique", _continue_to("gate"), {"gate": "gate", END: END})
    graph.add_conditional_edges("gate", _after_gate, {"design": "design", "extract": "extract", END: END})
    if checkpointer is None:
        connection = sqlite3.connect(data_dir() / "graph.sqlite3", check_same_thread=False)
        checkpointer = SqliteSaver(connection)
    return graph.compile(checkpointer=checkpointer)


solution_graph = build_graph()


def _config(room_id: str) -> dict:
    return {"configurable": {"thread_id": room_id}}


def start_room(room_id: str, organization: str, industry: str, transcript: str, model_mode: str | None = None) -> SolutionState:
    initial: SolutionState = {
        "room_id": room_id, "organization": organization, "industry": industry, "transcript": transcript,
        "model_mode": model_mode, "requirements": [], "use_cases": [], "open_items": [], "contradictions": [],
        "retrieved": [], "brief": None, "critique": None, "stages": [], "metrics": [], "decisions": [], "design_findings": [],
    }
    return solution_graph.invoke(initial, config=_config(room_id))


def resume_room(room_id: str, decision: dict) -> SolutionState:
    return solution_graph.invoke(Command(resume=decision), config=_config(room_id))


def room_is_waiting(room_id: str) -> bool:
    snapshot = solution_graph.get_state(_config(room_id))
    return bool(snapshot and snapshot.next and "gate" in snapshot.next)


def trace(room_id: str) -> list[dict]:
    history = list(solution_graph.get_state_history(_config(room_id)))
    history.reverse()
    steps: list[dict] = []
    previous_next: list[str] = []
    for snapshot in history:
        values = snapshot.values or {}
        steps.append({
            "step": (snapshot.metadata or {}).get("step"),
            "ran": previous_next,
            "next": list(snapshot.next),
            "interrupted": bool(snapshot.interrupts),
            "created_at": snapshot.created_at,
            "status": values.get("status"),
            "counts": {
                "utterances": len(values.get("utterances", []) or []),
                "requirements": len(values.get("requirements", []) or []),
                "open_items": len(values.get("open_items", []) or []),
                "retrieved": len(values.get("retrieved", []) or []),
                "findings": len(((values.get("critique") or {}).get("findings")) or []),
                "brief_revision": ((values.get("brief") or {}).get("revision")),
            },
        })
        previous_next = list(snapshot.next)
    return steps


# ----------------------------------------------------------------------------
# Projection
# ----------------------------------------------------------------------------


def to_room(state: SolutionState, created_at: str | None = None, fixture: str | None = None) -> Room:
    if state.get("status") == "approved":
        status = "approved"
    elif state.get("error"):
        status = "failed"
    else:
        status = "awaiting_review"
    stages = state.get("stages", [])
    metrics = RunMetrics(calls=[StageMetric(**item) for item in state.get("metrics", [])]).summary()
    now = _now()
    return Room(
        id=state["room_id"], organization=state["organization"], industry=state.get("industry", ""),
        status=status, created_at=created_at or now, updated_at=now, transcript=state["transcript"],
        utterances=state.get("utterances", []), speakers=state.get("speakers", []),
        requirements=state.get("requirements", []), use_cases=state.get("use_cases", []),
        open_items=state.get("open_items", []), contradictions=state.get("contradictions", []),
        grounding=state.get("grounding") or GroundingReport().model_dump(), retrieved=state.get("retrieved", []),
        brief=state.get("brief"), critique=state.get("critique"), stages=stages, metrics=metrics,
        review_note=state.get("review_note"), decisions=state.get("decisions", []), error=state.get("error"),
        fixture=fixture,
    )
