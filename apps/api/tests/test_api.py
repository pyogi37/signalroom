from fastapi.testclient import TestClient

from signalroom.main import app

client = TestClient(app)


def test_demo_requirements_are_grounded():
    response = client.get("/api/sessions/demo")
    assert response.status_code == 200
    requirements = response.json()["requirements"]
    assert requirements
    assert all(item["evidence"]["quote"] for item in requirements)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/capabilities").json()["local_fallback"] is True


def test_discovery_analysis_keeps_evidence_and_retrieves_context():
    response = client.post("/api/sessions/analyze", json={
        "organization": "Fictional Logistics",
        "transcript": "Operations lead: We need alerts when a shipment exception persists.\nIT architect: It must use our existing gateway API.\nSponsor: Success means reducing the time supervisors spend investigating each event.",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["requirements"]) == 3
    assert all(item["evidence"]["quote"] for item in data["requirements"])
    assert data["brief"]["retrieval"]
    assert data["stage"] == "approval"


def test_knowledge_can_be_indexed_and_searched():
    added = client.post("/api/knowledge", json={"title": "Synthetic safety note", "content": "Every automated decision must retain a reviewable source trail and a named human reviewer."})
    assert added.status_code == 201
    found = client.get("/api/knowledge/search", params={"query": "reviewable evidence trail"})
    assert found.status_code == 200
    assert found.json()


def test_session_is_persisted_and_approval_is_audited():
    analyzed = client.post("/api/sessions/analyze", json={
        "organization": "Persistent Fictional Co",
        "transcript": "Operations: We need to detect exceptions and notify an owner.\nIT: Use the existing API and keep an audit evidence history for every decision.",
    }).json()
    session_id = analyzed["id"]
    assert client.get(f"/api/sessions/{session_id}").status_code == 200
    approved = client.post(f"/api/sessions/{session_id}/review", json={"decision": "approve"})
    assert approved.json()["status"] == "approved"
    events = client.get(f"/api/sessions/{session_id}/audit").json()
    assert [event["event"] for event in events] == ["analysis_completed", "brief_approved"]


def test_text_document_upload():
    response = client.post(
        "/api/knowledge/upload",
        files={"file": ("guide.md", b"A synthetic integration guide requires authentication, rate limits, and evidence retention.", "text/markdown")},
    )
    assert response.status_code == 201
    assert response.json()["passages"] >= 1


def test_follow_up_reuses_the_persistent_session():
    analyzed = client.post("/api/sessions/analyze", json={
        "organization": "Follow Up Labs",
        "transcript": "Operations: Detect exceptions and notify the team through our existing API.",
    }).json()
    revised = client.post(f"/api/sessions/{analyzed['id']}/follow-up", json={"answers": [{
        "question": "What baseline and acceptance threshold will define PoC success?",
        "answer": "The owner approved a two-week baseline and a twenty-minute median investigation target.",
    }]})
    assert revised.status_code == 200
    assert revised.json()["id"] == analyzed["id"]


def test_voice_endpoint_explains_missing_provider_key():
    response = client.post("/api/audio/transcribe", files={"file": ("voice.webm", b"not-real-audio", "audio/webm")})
    assert response.status_code == 503


def test_evaluation_and_docx_export():
    analyzed = client.post("/api/sessions/analyze", json={
        "organization": "Export Example",
        "transcript": "Operations: Detect exceptions and retain evidence through the existing API.",
    }).json()
    evaluation = client.get(f"/api/sessions/{analyzed['id']}/evaluation").json()
    assert evaluation["grounding_rate"] == 1
    exported = client.get(f"/api/sessions/{analyzed['id']}/export.docx")
    assert exported.status_code == 200
    assert exported.content[:2] == b"PK"
    trace = client.get(f"/api/sessions/{analyzed['id']}/trace").json()
    assert len(trace) >= 5
