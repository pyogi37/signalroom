from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    speaker: str
    quote: str
    timestamp: str


class Requirement(BaseModel):
    id: str
    title: str
    detail: str
    kind: Literal["functional", "constraint", "success"]
    confidence: Literal["high", "medium", "low"]
    evidence: Evidence


class Risk(BaseModel):
    title: str
    severity: Literal["high", "medium", "low"]
    mitigation: str


class Session(BaseModel):
    id: str
    organization: str
    status: Literal["processing", "review", "approved"]
    stage: str
    progress: int = Field(ge=0, le=100)
    requirements: list[Requirement]
    open_questions: list[str]
    risks: list[Risk]
    brief: dict[str, object]
    stages: list[dict[str, object]]


class ReviewRequest(BaseModel):
    decision: Literal["approve", "request_changes"]
    note: str = ""


class AnalyzeRequest(BaseModel):
    organization: str = Field(min_length=2, max_length=100)
    transcript: str = Field(min_length=40, max_length=20_000)


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


class FollowUpAnswer(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    answer: str = Field(min_length=2, max_length=2_000)


class FollowUpRequest(BaseModel):
    answers: list[FollowUpAnswer] = Field(min_length=1, max_length=20)
