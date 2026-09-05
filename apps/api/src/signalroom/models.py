"""Domain models.

Two families live here. `Proposed*` and `*Draft` classes are what the model is
asked to produce; they are plain enough for strict JSON schema output (every
field required, enums as literals, no validation constraints). Everything
else is what the workflow stores after code has checked the model's output.
"""

from typing import Literal

from pydantic import BaseModel, Field

# ----------------------------------------------------------------------------
# Transcript
# ----------------------------------------------------------------------------


class Utterance(BaseModel):
    line: int
    speaker: str
    text: str
    origin: Literal["transcript", "follow_up"] = "transcript"


class SpeakerCount(BaseModel):
    speaker: str
    lines: int


# ----------------------------------------------------------------------------
# Model output: extraction
# ----------------------------------------------------------------------------


class ProposedEvidence(BaseModel):
    line: int
    quote: str


class ProposedRequirement(BaseModel):
    title: str
    detail: str
    kind: Literal["functional", "constraint", "success_measure"]
    evidence: ProposedEvidence
    confidence: Literal["high", "medium", "low"]
    confidence_reason: str


class ProposedUseCase(BaseModel):
    name: str
    trigger_condition: str
    expected_output: str
    evidence: ProposedEvidence


class ProposedOpenItem(BaseModel):
    question: str
    why_it_matters: str
    suggested_owner_role: str
    related_line: int | None


class ProposedContradiction(BaseModel):
    topic: str
    line_a: int
    line_b: int
    note: str


class ProposedResolution(BaseModel):
    open_item_id: str
    resolved_by_line: int
    note: str


class Extraction(BaseModel):
    requirements: list[ProposedRequirement]
    use_cases: list[ProposedUseCase]
    open_items: list[ProposedOpenItem]
    contradictions: list[ProposedContradiction]
    resolutions: list[ProposedResolution]


# ----------------------------------------------------------------------------
# Checked extraction
# ----------------------------------------------------------------------------


class Evidence(BaseModel):
    line: int
    speaker: str
    quote: str


class Requirement(BaseModel):
    id: str
    title: str
    detail: str
    kind: Literal["functional", "constraint", "success_measure"]
    confidence: Literal["high", "medium", "low"]
    confidence_reason: str
    evidence: Evidence


class UseCase(BaseModel):
    id: str
    name: str
    trigger_condition: str
    expected_output: str
    evidence: Evidence


class OpenItem(BaseModel):
    id: str
    question: str
    why_it_matters: str
    suggested_owner_role: str
    related_line: int | None = None
    status: Literal["open", "answered"] = "open"
    answer: str | None = None
    answered_line: int | None = None
    rejected_answers: list[str] = Field(default_factory=list)


class Contradiction(BaseModel):
    topic: str
    line_a: int
    line_b: int
    note: str


class GroundingDrop(BaseModel):
    kind: Literal["requirement", "use_case"]
    title: str
    reason: Literal["line_out_of_range", "quote_not_on_line", "quote_not_in_transcript", "empty_quote"]
    proposed_line: int
    proposed_quote: str


class GroundingRepair(BaseModel):
    kind: Literal["requirement", "use_case"]
    title: str
    proposed_line: int
    actual_line: int


class GroundingReport(BaseModel):
    proposed: int = 0
    passed: int = 0
    repaired: int = 0
    dropped: int = 0
    drops: list[GroundingDrop] = Field(default_factory=list)
    repairs: list[GroundingRepair] = Field(default_factory=list)


# ----------------------------------------------------------------------------
# Retrieval
# ----------------------------------------------------------------------------


class KnowledgeDocument(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    content: str = Field(min_length=30, max_length=20_000)
    source: str = "uploaded reference"


class SearchHit(BaseModel):
    passage_id: str
    title: str
    passage: str
    score: float
    source: str
    shared_terms: int = 0
    supports: list[str] = Field(default_factory=list)


# ----------------------------------------------------------------------------
# Model output: brief
# ----------------------------------------------------------------------------


class Snapshot(BaseModel):
    one_line_goal: str
    scope_summary: str
    deployment_shape: str
    stakeholder_roles: list[str]


class ReadinessAssessment(BaseModel):
    use_case_id: str
    readiness: Literal["proven_pattern", "needs_feasibility_check", "unknown"]
    note: str
    cited_passage_ids: list[str]


class Constraint(BaseModel):
    constraint: str
    source: Literal["transcript", "pattern_library", "assumption"]
    line: int | None
    passage_id: str | None


class Phase(BaseModel):
    name: str
    purpose: str
    duration: str
    exit_criteria: list[str]


class Recommendation(BaseModel):
    approach: str
    phases: list[Phase]
    discussed_not_in_scope: list[str]


class SuccessMeasure(BaseModel):
    measure: str
    baseline_status: Literal["confirmed", "not_stated", "to_be_confirmed"]
    owner_role: str
    line: int | None


class Risk(BaseModel):
    title: str
    severity: Literal["high", "medium", "low"]
    mitigation: str
    basis: str


class BriefDraft(BaseModel):
    snapshot: Snapshot
    readiness: list[ReadinessAssessment]
    constraints: list[Constraint]
    recommendation: Recommendation
    success_measures: list[SuccessMeasure]
    risks: list[Risk]
    additional_open_items: list[ProposedOpenItem]


class Brief(BaseModel):
    snapshot: Snapshot
    readiness: list[ReadinessAssessment]
    constraints: list[Constraint]
    recommendation: Recommendation
    success_measures: list[SuccessMeasure]
    risks: list[Risk]
    revision: int = 1


# ----------------------------------------------------------------------------
# Model output: critique
# ----------------------------------------------------------------------------

FindingKind = Literal[
    "unsupported_claim", "contradiction", "missing_owner", "scope_creep", "overclaim",
    "unverified_number", "dropped_evidence", "invalid_citation",
]


class ProposedFinding(BaseModel):
    kind: Literal["unsupported_claim", "contradiction", "missing_owner", "scope_creep", "overclaim"]
    severity: Literal["high", "medium", "low"]
    text: str
    location: str
    lines: list[int]


class CritiqueDraft(BaseModel):
    findings: list[ProposedFinding]
    verdict: Literal["ready_for_review", "needs_changes"]
    summary: str


class Finding(BaseModel):
    kind: FindingKind
    severity: Literal["high", "medium", "low"]
    text: str
    location: str
    lines: list[int] = Field(default_factory=list)
    source: Literal["model", "code"]


class Critique(BaseModel):
    findings: list[Finding]
    verdict: Literal["ready_for_review", "needs_changes"]
    summary: str


# ----------------------------------------------------------------------------
# Run bookkeeping
# ----------------------------------------------------------------------------


class StageRecord(BaseModel):
    name: str
    status: Literal["complete", "active", "failed", "pending"]
    detail: str
    latency_ms: float = 0.0


class StageMetric(BaseModel):
    stage: str
    mode: str
    model: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None = None


class RunMetrics(BaseModel):
    calls: list[StageMetric] = Field(default_factory=list)

    @property
    def total_latency_ms(self) -> float:
        return round(sum(call.latency_ms for call in self.calls), 1)

    @property
    def total_input_tokens(self) -> int:
        return sum(call.input_tokens for call in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(call.output_tokens for call in self.calls)

    @property
    def total_cost_usd(self) -> float | None:
        costs = [call.estimated_cost_usd for call in self.calls]
        if not costs or any(cost is None for cost in costs):
            return None
        return round(sum(cost for cost in costs if cost is not None), 6)

    def summary(self) -> dict:
        return {
            "calls": [call.model_dump() for call in self.calls],
            "total_latency_ms": self.total_latency_ms,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "modes": sorted({call.mode for call in self.calls}),
        }


class Decision(BaseModel):
    kind: Literal["approve", "request_changes", "follow_up"]
    note: str = ""
    decided_at: str


# ----------------------------------------------------------------------------
# Room: what the API stores and returns
# ----------------------------------------------------------------------------

RoomStatus = Literal["awaiting_review", "approved", "failed"]


class Room(BaseModel):
    id: str
    organization: str
    industry: str
    status: RoomStatus
    created_at: str
    updated_at: str
    transcript: str
    utterances: list[Utterance]
    speakers: list[SpeakerCount]
    requirements: list[Requirement]
    use_cases: list[UseCase]
    open_items: list[OpenItem]
    contradictions: list[Contradiction]
    grounding: GroundingReport
    retrieved: list[SearchHit]
    brief: Brief | None
    critique: Critique | None
    stages: list[StageRecord]
    metrics: dict
    review_note: str | None = None
    decisions: list[Decision] = Field(default_factory=list)
    error: str | None = None
    synthetic: bool = True
    fixture: str | None = None


# ----------------------------------------------------------------------------
# API requests
# ----------------------------------------------------------------------------


class CreateRoomRequest(BaseModel):
    organization: str = Field(min_length=2, max_length=100)
    industry: str = Field(default="", max_length=100)
    transcript: str = Field(min_length=40, max_length=30_000)


class FollowUpAnswer(BaseModel):
    open_item_id: str = Field(min_length=2, max_length=20)
    answer: str = Field(min_length=1, max_length=2_000)


class DecisionRequest(BaseModel):
    kind: Literal["approve", "request_changes", "follow_up"]
    note: str = Field(default="", max_length=2_000)
    answers: list[FollowUpAnswer] = Field(default_factory=list, max_length=20)
    answered_by: str = Field(default="Follow-up answer", min_length=2, max_length=60)
