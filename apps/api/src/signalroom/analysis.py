import re
from uuid import uuid4

from .llm import extract_with_live_model
from .models import AnalyzeRequest, Evidence, Requirement, Risk, Session
from .retrieval import store
from .workflow import run_solution_graph


def _evidence(transcript: str, keywords: tuple[str, ...]) -> Evidence | None:
    for index, raw in enumerate(transcript.splitlines()):
        line = raw.strip()
        if line and any(word in line.lower() for word in keywords):
            speaker, _, quote = line.partition(":")
            if not quote:
                speaker, quote = "Discovery participant", line
            return Evidence(speaker=speaker.strip(), quote=quote.strip(), timestamp=f"line {index + 1}")
    return None


def analyze(request: AnalyzeRequest, session_id: str | None = None) -> Session:
    current_session_id = session_id or str(uuid4())
    hits = store.search(request.transcript)
    retrieved_context = "\n".join(f"[{hit.title}] {hit.passage}" for hit in hits)
    live = extract_with_live_model(request.transcript, retrieved_context)
    candidates = [
        ("REQ-01", "Integrate with existing systems", "Use the existing operational interface instead of replacing installed infrastructure.", "constraint", ("existing", "api", "gateway", "integrat")),
        ("REQ-02", "Detect and surface operational exceptions", "Identify important operational exceptions and notify the responsible reviewer.", "functional", ("alert", "detect", "notify", "exception", "excursion")),
        ("REQ-03", "Measure workflow improvement", "Compare the assisted workflow against an agreed baseline during the PoC.", "success", ("metric", "success", "reduce", "faster", "hour", "time")),
        ("REQ-04", "Retain an evidence trail", "Keep the source evidence and decision history available for review.", "functional", ("audit", "evidence", "history", "trace", "compliance")),
    ]
    requirements = []
    if live:
        for index, item in enumerate(live.requirements):
            if item.evidence_quote not in request.transcript:
                continue
            requirements.append(Requirement(id=f"REQ-{index + 1:02}", title=item.title, detail=item.detail, kind=item.kind, confidence=item.confidence, evidence=Evidence(speaker=item.speaker, quote=item.evidence_quote, timestamp="verified quote")))
    else:
        for identifier, title, detail, kind, keywords in candidates:
            evidence = _evidence(request.transcript, keywords)
            if evidence:
                requirements.append(Requirement(id=identifier, title=title, detail=detail, kind=kind, confidence="high" if len(evidence.quote) > 45 else "medium", evidence=evidence))
    if not requirements:
        first = next((line.strip() for line in request.transcript.splitlines() if len(line.strip()) > 20), request.transcript[:200])
        requirements.append(Requirement(id="REQ-01", title="Clarify the primary operational outcome", detail="The discovery contains an objective but needs a more specific measurable workflow outcome.", kind="success", confidence="low", evidence=Evidence(speaker="Discovery participant", quote=first, timestamp="line 1")))

    open_questions = list(live.open_questions) if live else []
    lower = request.transcript.lower()
    for needle, question in [
        ("baseline", "What baseline and acceptance threshold will define PoC success?"),
        ("authentication", "What authentication and authorization model does the existing interface use?"),
        ("owner", "Who owns review, acknowledgement, and escalation decisions?"),
    ]:
        if not live and needle not in lower:
            open_questions.append(question)

    risks = [Risk(**item.model_dump()) for item in live.risks] if live else [Risk(title="Evidence coverage", severity="medium", mitigation="Keep low-confidence requirements in review until a participant confirms them.")]
    if not live and ("alert" in lower or "notify" in lower):
        risks.append(Risk(title="Alert fatigue", severity="high", mitigation="Calibrate thresholds on historical data before enabling live notifications."))
    architecture = ["Discovery evidence", "Requirement extractor", "Vector knowledge store", "Solution graph", "Human review"]
    graph_result = run_solution_graph({
        "transcript": request.transcript,
        "requirements": [{"id": item.id, "evidence": item.evidence.model_dump()} for item in requirements],
        "retrieved_evidence": [hit.model_dump() for hit in hits],
        "architecture": architecture,
        "risks": [risk.model_dump() for risk in risks],
    }, current_session_id)
    return Session(
        id=current_session_id, organization=request.organization, status="review", stage="approval" if graph_result["ready_for_review"] else "critique", progress=86 if graph_result["ready_for_review"] else 72,
        requirements=requirements, open_questions=open_questions, risks=risks,
        brief={"problem": requirements[0].evidence.quote, "recommendation": live.recommendation if live else "Run a bounded PoC that validates integration feasibility, evidence quality, and one measurable operational outcome before production design.", "architecture": architecture, "success": ["All requirements retain source evidence", "Open questions have named owners", "PoC result is measured against a confirmed baseline"], "retrieval": [hit.model_dump() for hit in hits], "transcript": request.transcript, "execution_mode": "live model" if live else "deterministic local"},
        stages=[
            {"name": "Discover", "status": "complete", "detail": f"{len(request.transcript.splitlines())} transcript lines"},
            {"name": "Structure", "status": "complete", "detail": f"{len(requirements)} grounded requirements"},
            {"name": "Retrieve", "status": "complete", "detail": f"{len(hits)} vector search results"},
            {"name": "Design", "status": "complete", "detail": "PoC architecture proposed"},
            {"name": "Critique", "status": "complete", "detail": f"{len(risks)} risks reviewed"},
            {"name": "Approve", "status": "active", "detail": "Waiting for solution engineer"},
        ],
    )
