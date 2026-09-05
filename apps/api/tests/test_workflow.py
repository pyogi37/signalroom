"""End-to-end workflow tests against a fake model.

The fake answers each stage with canned structured output that deliberately
includes one invented quote, one number that is nowhere in the transcript,
and one citation to a passage that was never retrieved, so the tests prove
the code checks fire and the human gate behaves as an interrupt.
"""

import re

import pytest
from fastapi.testclient import TestClient

from signalroom import workflow
from signalroom.model_client import ModelCall, ModelUnavailable
from signalroom.models import (
    BriefDraft,
    Constraint,
    CritiqueDraft,
    Extraction,
    Phase,
    ProposedContradiction,
    ProposedEvidence,
    ProposedFinding,
    ProposedOpenItem,
    ProposedRequirement,
    ProposedResolution,
    ProposedUseCase,
    ReadinessAssessment,
    Recommendation,
    Risk,
    Snapshot,
    SuccessMeasure,
)

TRANSCRIPT = (
    "Operations lead: We usually discover an excursion when the shift report is already being written.\n"
    "IT architect: The gateway is staying. Anything new has to consume its API.\n"
    "Sponsor: A supervisor can lose most of an hour piecing together one event.\n"
    "IT architect: To be honest we might replace the gateway next year.\n"
    "Operations lead: Alerts should go to whoever is on shift, and we need to know why each one fired.\n"
)


def fake_structured_call(stage, system, user, schema, *, temperature=0.0, max_output_tokens=8192, mode=None):
    call = ModelCall(stage=stage, model="fake-model", mode="replay", latency_ms=12.5, input_tokens=100, output_tokens=50,
                     estimated_cost_usd=None, recording_key="fake")
    if schema is Extraction:
        lines = [int(match) for match in re.findall(r"\[L(\d+)\]", user)]
        follow_up_line = max(lines) if "Previous open items" in user else None
        resolutions = [ProposedResolution(open_item_id="OI-01", resolved_by_line=follow_up_line, note="answered")] if follow_up_line else []
        return Extraction(
            requirements=[
                ProposedRequirement(title="Detect excursions before the shift report", detail="Notify during the shift.", kind="functional",
                                    evidence=ProposedEvidence(line=1, quote="discover an excursion when the shift report is already being written"),
                                    confidence="high", confidence_reason="explicit"),
                ProposedRequirement(title="Consume the existing gateway API", detail="No new sensors.", kind="constraint",
                                    evidence=ProposedEvidence(line=3, quote="Anything new has to consume its API"),
                                    confidence="high", confidence_reason="explicit"),
                ProposedRequirement(title="Cut investigation time by 40%", detail="Invented.", kind="success_measure",
                                    evidence=ProposedEvidence(line=3, quote="cut investigation time by 40%"),
                                    confidence="medium", confidence_reason="invented"),
            ],
            use_cases=[ProposedUseCase(name="Excursion alert", trigger_condition="temperature outside range", expected_output="notify on-shift staff",
                                       evidence=ProposedEvidence(line=5, quote="Alerts should go to whoever is on shift"))],
            open_items=[ProposedOpenItem(question="What baseline exists for investigation time?", why_it_matters="success measure", suggested_owner_role="Sponsor", related_line=3)],
            contradictions=[ProposedContradiction(topic="Gateway future", line_a=2, line_b=4, note="stays vs replaced")],
            resolutions=resolutions,
        ), call
    if schema is BriefDraft:
        offered = re.findall(r"^\[([a-z0-9-]+#\d+)\]", user, flags=re.M)
        first_offered = offered[0] if offered else "operational-alert-design#1"
        return BriefDraft(
            snapshot=Snapshot(one_line_goal="Detect excursions during the shift", scope_summary="One site", deployment_shape="TBC", stakeholder_roles=["Operations lead", "IT architect", "Sponsor"]),
            readiness=[ReadinessAssessment(use_case_id="UC-01", readiness="proven_pattern", note="alerting pattern", cited_passage_ids=[first_offered, "not-real#1"])],
            constraints=[Constraint(constraint="Existing gateway stays", source="transcript", line=2, passage_id=None)],
            recommendation=Recommendation(approach="Run a 6 week validation pilot" + (" (revised)" if "Review note" in user else ""),
                                          phases=[Phase(name="Validate", purpose="prove ingestion", duration="TBC", exit_criteria=["alerts retain evidence"])],
                                          discussed_not_in_scope=[]),
            success_measures=[SuccessMeasure(measure="Investigation time against baseline", baseline_status="not_stated", owner_role="Sponsor", line=3)],
            risks=[Risk(title="Alert fatigue", severity="medium", mitigation="calibrate on history", basis="L5")],
            additional_open_items=[ProposedOpenItem(question="Who acknowledges an alert?", why_it_matters="escalation", suggested_owner_role="Operations lead", related_line=5)],
        ), call
    if schema is CritiqueDraft:
        return CritiqueDraft(
            findings=[ProposedFinding(kind="overclaim", severity="low", text="Deployment shape stated confidently", location="snapshot", lines=[2])],
            verdict="ready_for_review", summary="Grounded, one number to fix.",
        ), call
    raise AssertionError(f"unexpected schema {schema}")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(workflow, "structured_call", fake_structured_call)
    from signalroom.main import app
    return TestClient(app)


def create(client, organization="Fixture Cold Chain"):
    response = client.post("/api/rooms", json={"organization": organization, "industry": "cold storage", "transcript": TRANSCRIPT})
    assert response.status_code == 201, response.text
    return response.json()


def test_room_runs_to_the_gate_with_checks_applied(client):
    room = create(client)
    assert room["status"] == "awaiting_review"
    assert [stage["name"] for stage in room["stages"]] == ["Discover", "Extract", "Retrieve", "Design", "Critique", "Gate"]
    assert room["stages"][-1]["status"] == "active"

    assert [item["id"] for item in room["requirements"]] == ["REQ-01", "REQ-02"]
    assert room["requirements"][1]["evidence"]["line"] == 2, "quote proposed for L3 is repaired to L2"
    assert room["grounding"] == {**room["grounding"], "proposed": 4, "passed": 3, "repaired": 1, "dropped": 1}
    assert room["grounding"]["drops"][0]["title"] == "Cut investigation time by 40%"
    assert room["use_cases"][0]["evidence"]["speaker"] == "Operations lead"

    assert [item["id"] for item in room["open_items"]] == ["OI-01", "OI-02"]
    assert room["brief"]["revision"] == 1
    assert room["retrieved"], "alert and gateway requirements should retrieve pattern passages"
    assert room["brief"]["readiness"][0]["cited_passage_ids"] == [room["retrieved"][0]["passage_id"]], "the invented citation is stripped, the real one kept"

    kinds = {(item["kind"], item["source"]) for item in room["critique"]["findings"]}
    assert ("unverified_number", "code") in kinds
    assert ("invalid_citation", "code") in kinds
    assert ("dropped_evidence", "code") in kinds
    assert ("contradiction", "code") in kinds
    assert ("overclaim", "model") in kinds
    assert room["critique"]["verdict"] == "needs_changes", "an unverified number is a high finding"
    assert room["metrics"]["calls"] and room["metrics"]["modes"] == ["replay"]
    assert len(room["metrics"]["calls"]) == 3


def test_trace_shows_real_steps_and_the_interrupt(client):
    room = create(client)
    steps = client.get(f"/api/rooms/{room['id']}/trace").json()
    ran = [node for step in steps for node in step["ran"]]
    assert ran[:6] == ["__start__", "discover", "extract", "retrieve", "design", "critique"]
    assert steps[-1]["next"] == ["gate"] and steps[-1]["interrupted"] is True
    assert steps[-1]["counts"]["requirements"] == 2


def test_non_answer_keeps_item_open_and_real_answer_closes_it(client):
    room = create(client)
    vague = client.post(f"/api/rooms/{room['id']}/decision", json={"kind": "follow_up", "answers": [{"open_item_id": "OI-01", "answer": "We don't know yet"}]})
    assert vague.status_code == 200, vague.text
    after_vague = vague.json()
    assert after_vague["open_items"][0]["status"] == "open"
    assert after_vague["open_items"][0]["rejected_answers"] == ["We don't know yet"]
    assert after_vague["utterances"][-1]["origin"] == "follow_up"
    assert after_vague["brief"]["revision"] == 2
    assert after_vague["status"] == "awaiting_review"

    real = client.post(f"/api/rooms/{room['id']}/decision", json={"kind": "follow_up", "answered_by": "Sponsor (email)",
                                                                  "answers": [{"open_item_id": "OI-01", "answer": "The shift log from the last two quarters is the baseline."}]})
    after_real = real.json()
    assert after_real["open_items"][0]["status"] == "answered"
    assert after_real["utterances"][-1]["speaker"] == "Sponsor (email)"
    assert after_real["brief"]["revision"] == 3
    assert [decision["kind"] for decision in after_real["decisions"]] == ["follow_up", "follow_up"]


def test_request_changes_revises_and_approve_ends_the_graph(client):
    room = create(client)
    revised = client.post(f"/api/rooms/{room['id']}/decision", json={"kind": "request_changes", "note": "State the deployment shape as TBC"}).json()
    assert revised["status"] == "awaiting_review"
    assert revised["brief"]["revision"] == 2
    assert "(revised)" in revised["brief"]["recommendation"]["approach"]
    assert revised["stages"][-1]["status"] == "active"

    approved = client.post(f"/api/rooms/{room['id']}/decision", json={"kind": "approve"}).json()
    assert approved["status"] == "approved"
    assert approved["stages"][-1]["detail"] == "Approved by the solution engineer"
    again = client.post(f"/api/rooms/{room['id']}/decision", json={"kind": "approve"})
    assert again.status_code == 409
    events = [event["event"] for event in client.get(f"/api/rooms/{room['id']}/audit").json()]
    assert events == ["room_created", "changes_requested", "brief_approved"]


def test_decision_validation(client):
    room = create(client)
    assert client.post(f"/api/rooms/{room['id']}/decision", json={"kind": "request_changes", "note": "  "}).status_code == 422
    assert client.post(f"/api/rooms/{room['id']}/decision", json={"kind": "follow_up", "answers": []}).status_code == 422
    assert client.post(f"/api/rooms/{room['id']}/decision", json={"kind": "follow_up", "answers": [{"open_item_id": "OI-99", "answer": "x y z w"}]}).status_code == 422
    assert client.post("/api/rooms/missing/decision", json={"kind": "approve"}).status_code == 404


def test_export_and_listing(client):
    room = create(client, organization="Export Co")
    exported = client.get(f"/api/rooms/{room['id']}/export.docx")
    assert exported.status_code == 200 and exported.content[:2] == b"PK"
    listing = client.get("/api/rooms").json()
    assert listing[0]["organization"] == "Export Co" and listing[0]["open_items"] == 2


def test_missing_model_is_a_clear_503_and_nothing_is_stored(monkeypatch):
    def unavailable(*args, **kwargs):
        raise ModelUnavailable("Set GROQ_API_KEY to analyse new transcripts")
    monkeypatch.setattr(workflow, "structured_call", unavailable)
    from signalroom.main import app
    client = TestClient(app)
    before = len(client.get("/api/rooms").json())
    response = client.post("/api/rooms", json={"organization": "No Key Co", "industry": "", "transcript": TRANSCRIPT})
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]
    assert len(client.get("/api/rooms").json()) == before


def test_capabilities_and_knowledge_endpoints(client):
    capabilities = client.get("/api/capabilities").json()
    assert capabilities["live"] is False and capabilities["synthetic_only"] is True
    added = client.post("/api/knowledge", json={"title": "Synthetic safety note", "content": "Every automated decision must retain a reviewable source trail and a named human reviewer."})
    assert added.status_code == 201
    found = client.get("/api/knowledge/search", params={"query": "reviewable source trail for automated decisions"}).json()
    assert found and found[0]["passage_id"].startswith("synthetic-safety-note#")
    upload = client.post("/api/knowledge/upload", files={"file": ("guide.md", b"A synthetic integration guide requires authentication, rate limits, and evidence retention.", "text/markdown")})
    assert upload.status_code == 201 and upload.json()["passages"] >= 1
    assert client.get("/api/evaluation/latest").status_code in (200, 404)
