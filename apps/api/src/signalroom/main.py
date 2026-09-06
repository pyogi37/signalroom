import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import env
from .documents import extract_text
from .exports import brief_docx
from .fixtures import load_fixtures
from .model_client import describe as describe_model
from .models import CreateRoomRequest, DecisionRequest, KnowledgeDocument, Room, SearchHit
from .persistence import audit_events, get_room, list_rooms, log_event, save_room
from .retrieval import store
from .seeding import seed_rooms
from .workflow import resume_room, room_is_waiting, start_room, to_room, trace

log = logging.getLogger("signalroom")
RESULTS_PATH = Path(__file__).resolve().parents[2] / "evals" / "results" / "latest.json"



@asynccontextmanager
async def lifespan(_: FastAPI):
    if env("SIGNALROOM_SKIP_SEED") != "1":
        outcome = seed_rooms()
        if outcome["seeded"] or outcome["skipped"]:
            log.info("Seeded rooms %s; skipped %s", outcome["seeded"], outcome["skipped"])
    yield


app = FastAPI(title="SignalRoom API", version="0.3.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    # Any localhost origin during development; set SIGNALROOM_CORS_ORIGINS for anything else.
    allow_origins=[origin.strip() for origin in env("SIGNALROOM_CORS_ORIGINS").split(",") if origin.strip()],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/capabilities")
def capabilities() -> dict:
    return {**describe_model(), "synthetic_only": True}


@app.get("/api/rooms")
def rooms() -> list[dict]:
    return list_rooms()


@app.get("/api/fixtures")
def fixtures() -> list[dict]:
    """Synthetic example transcripts the composer can load. All invented."""
    return [
        {"id": item.id, "organization": item.organization, "industry": item.industry, "transcript": item.transcript,
         "lines": len(item.transcript.splitlines()), "seeded": item.seed}
        for item in load_fixtures()
    ]


@app.post("/api/rooms", response_model=Room, status_code=201)
def create_room(request: CreateRoomRequest) -> Room:
    room_id = uuid4().hex[:12]
    state = start_room(room_id, request.organization.strip(), request.industry.strip(), request.transcript)
    if state.get("error"):
        status = 503 if state.get("error_kind") == "model_unavailable" else 502
        raise HTTPException(status_code=status, detail=state["error"])
    room = save_room(to_room(state))
    log_event(room.id, "room_created", {"metrics": room.metrics, "grounding": room.grounding.model_dump(), "stages": [stage.model_dump() for stage in room.stages]})
    return room


@app.get("/api/rooms/{room_id}", response_model=Room)
def read_room(room_id: str) -> Room:
    room = get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@app.post("/api/rooms/{room_id}/decision", response_model=Room)
def decide(room_id: str, request: DecisionRequest) -> Room:
    room = get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room.status == "approved":
        raise HTTPException(status_code=409, detail="This brief is already approved")
    if room.status == "failed":
        raise HTTPException(status_code=409, detail="This room failed during a model stage; start a new room")
    if not room_is_waiting(room_id):
        raise HTTPException(status_code=409, detail="This room is not waiting at the gate")
    if request.kind == "follow_up":
        open_ids = {item.id for item in room.open_items if item.status == "open"}
        unknown = [answer.open_item_id for answer in request.answers if answer.open_item_id not in open_ids]
        if not request.answers:
            raise HTTPException(status_code=422, detail="Add at least one answer to an open item")
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown or already answered open items: {', '.join(unknown)}")
    if request.kind == "request_changes" and not request.note.strip():
        raise HTTPException(status_code=422, detail="Say what should change")

    state = resume_room(room_id, request.model_dump())
    updated = save_room(to_room(state, created_at=room.created_at, fixture=room.fixture))
    event = {"approve": "brief_approved", "request_changes": "changes_requested", "follow_up": "follow_up_added"}[request.kind]
    log_event(room_id, event, {"note": request.note, "answers": len(request.answers), "status": updated.status, "error": updated.error}, actor="solution engineer")
    return updated


@app.get("/api/rooms/{room_id}/trace")
def read_trace(room_id: str) -> list[dict]:
    if not get_room(room_id):
        raise HTTPException(status_code=404, detail="Room not found")
    return trace(room_id)


@app.get("/api/rooms/{room_id}/audit")
def read_audit(room_id: str) -> list[dict]:
    if not get_room(room_id):
        raise HTTPException(status_code=404, detail="Room not found")
    return audit_events(room_id)


@app.get("/api/rooms/{room_id}/export.docx")
def export_brief(room_id: str) -> StreamingResponse:
    room = get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    filename = f"signalroom-{room.organization.lower().replace(' ', '-')}-r{room.brief.revision if room.brief else 0}.docx"
    return StreamingResponse(
        brief_docx(room),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/knowledge", status_code=201)
def add_knowledge(document: KnowledgeDocument) -> dict[str, int | str]:
    return {"status": "indexed", "title": document.title, "passages": store.add(document)}


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
        content=text[:20_000],
        source=f"uploaded reference: {file.filename or 'document'}",
    )
    return {"status": "indexed", "title": document.title, "passages": store.add(document)}


@app.get("/api/knowledge/search", response_model=list[SearchHit])
def search_knowledge(query: str, limit: int = 4) -> list[SearchHit]:
    return store.search(query, min(max(limit, 1), 12))


@app.get("/api/evaluation/latest")
def latest_evaluation() -> dict:
    if not RESULTS_PATH.exists():
        raise HTTPException(status_code=404, detail="No evaluation results have been recorded yet")
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
