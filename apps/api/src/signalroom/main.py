from time import perf_counter

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .analysis import analyze
from .demo import demo_session
from .documents import extract_text
from .evaluation import evaluate
from .exports import brief_docx
from .llm import live_model_enabled
from .models import AnalyzeRequest, FollowUpRequest, KnowledgeDocument, ReviewRequest, SearchHit, Session
from .persistence import audit_events, get_session, log_event, recent_sessions, save_session
from .retrieval import store
from .workflow import graph_history

app = FastAPI(title="SignalRoom API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
save_session(demo_session())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/capabilities")
def capabilities() -> dict[str, bool]:
    return {"llm": live_model_enabled(), "local_fallback": True}


@app.get("/api/sessions/demo", response_model=Session)
def get_demo_session() -> Session:
    return demo_session()


@app.get("/api/sessions")
def list_sessions() -> list[dict[str, str]]:
    return recent_sessions()


@app.get("/api/sessions/{session_id}", response_model=Session)
def read_session(session_id: str) -> Session:
    found = get_session(session_id)
    if not found:
        raise HTTPException(status_code=404, detail="Session not found")
    return found


@app.post("/api/sessions/analyze", response_model=Session)
def analyze_discovery(request: AnalyzeRequest) -> Session:
    started = perf_counter()
    session = save_session(analyze(request))
    log_event(session.id, "analysis_completed", {
        "requirements": len(session.requirements),
        "open_questions": len(session.open_questions),
        "retrieval_hits": len(session.brief.get("retrieval", [])),
        "duration_ms": round((perf_counter() - started) * 1000, 2),
        "execution_mode": session.brief.get("execution_mode", "demo fixture"),
    })
    return session


@app.post("/api/sessions/{session_id}/follow-up", response_model=Session)
def answer_follow_up(session_id: str, request: FollowUpRequest) -> Session:
    current = get_session(session_id)
    if not current:
        raise HTTPException(status_code=404, detail="Session not found")
    transcript = str(current.brief.get("transcript", ""))
    additions = "\n".join(f"Follow-up — {item.question}: {item.answer}" for item in request.answers)
    revised = analyze(AnalyzeRequest(organization=current.organization, transcript=f"{transcript}\n{additions}"), session_id=current.id)
    save_session(revised)
    log_event(session_id, "follow_up_analyzed", {"answers": len(request.answers), "remaining_questions": len(revised.open_questions)})
    return revised


@app.post("/api/knowledge", status_code=201)
def add_knowledge(document: KnowledgeDocument) -> dict[str, int | str]:
    return {"status": "indexed", "passages": store.add(document)}


@app.post("/api/knowledge/upload", status_code=201)
async def upload_knowledge(file: UploadFile = File(...), title: str = Form("")) -> dict[str, int | str]:
    try:
        text = await extract_text(file)
    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error
    if len(text.strip()) < 30:
        raise HTTPException(status_code=422, detail="No usable text could be extracted")
    document = KnowledgeDocument(
        title=title.strip() or file.filename or "Uploaded document",
        content=text,
        source=file.filename or "uploaded document",
    )
    return {"status": "indexed", "title": document.title, "passages": store.add(document)}


@app.get("/api/knowledge/search", response_model=list[SearchHit])
def search_knowledge(query: str, limit: int = 4) -> list[SearchHit]:
    return store.search(query, min(max(limit, 1), 12))


@app.post("/api/sessions/{session_id}/review", response_model=Session)
def review_session(session_id: str, request: ReviewRequest) -> Session:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "review":
        raise HTTPException(status_code=409, detail="Session is not awaiting review")
    if request.decision == "approve":
        session.status = "approved"
        session.progress = 100
        session.stages[-1] = {"name": "Approve", "status": "complete", "detail": "Approved by solution engineer"}
    else:
        session.stage = "critique"
        session.progress = 74
        session.stages[-1] = {"name": "Approve", "status": "blocked", "detail": request.note or "Changes requested"}
    save_session(session)
    log_event(session.id, "brief_approved" if request.decision == "approve" else "changes_requested", {"note": request.note})
    return session


@app.get("/api/sessions/{session_id}/audit")
def read_audit(session_id: str) -> list[dict[str, object]]:
    if not get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return audit_events(session_id)


@app.get("/api/sessions/{session_id}/trace")
def read_trace(session_id: str) -> list[dict]:
    if not get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return graph_history(session_id)


@app.get("/api/sessions/{session_id}/evaluation")
def read_evaluation(session_id: str) -> dict[str, int | float | bool | str]:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return evaluate(session)


@app.get("/api/sessions/{session_id}/export.docx")
def export_brief(session_id: str) -> StreamingResponse:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    filename = f"signalroom-{session.organization.lower().replace(' ', '-')}.docx"
    return StreamingResponse(
        brief_docx(session),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
