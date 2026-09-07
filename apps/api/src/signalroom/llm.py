import os
from typing import Literal

from pydantic import BaseModel, Field


class LLMRequirement(BaseModel):
    title: str
    detail: str
    kind: Literal["functional", "constraint", "success"]
    confidence: Literal["high", "medium", "low"]
    evidence_quote: str
    speaker: str


class LLMRisk(BaseModel):
    title: str
    severity: Literal["high", "medium", "low"]
    mitigation: str


class LLMExtraction(BaseModel):
    requirements: list[LLMRequirement] = Field(max_length=12)
    open_questions: list[str] = Field(max_length=10)
    risks: list[LLMRisk] = Field(max_length=8)
    recommendation: str


def live_model_enabled() -> bool:
    return os.getenv("SIGNALROOM_LLM_PROVIDER", "local") == "openai" and bool(os.getenv("OPENAI_API_KEY"))


def extract_with_live_model(transcript: str, retrieved_context: str) -> LLMExtraction | None:
    if not live_model_enabled():
        return None
    from openai import OpenAI

    response = OpenAI().responses.parse(
        model=os.getenv("SIGNALROOM_OPENAI_MODEL", "gpt-5-mini"),
        instructions=(
            "You are a solutioning analyst. Extract only claims explicitly supported by the transcript. "
            "Evidence quotes must be exact substrings of the transcript. Retrieved context may inform risks "
            "and recommendations but must never be presented as a customer statement. Preserve unknowns as questions."
        ),
        input=f"DISCOVERY TRANSCRIPT\n{transcript}\n\nRETRIEVED REFERENCE CONTEXT\n{retrieved_context}",
        text_format=LLMExtraction,
    )
    return response.output_parsed
