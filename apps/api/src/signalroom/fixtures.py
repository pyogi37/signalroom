"""Synthetic discovery fixtures shared by the demo seed and the evaluation suite.

Every fixture is invented. The `gold` block is the labelled answer key: which
requirements and open items a careful solution engineer would have written
down, and which traps were planted in the transcript or the reference
library.
"""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "evals" / "fixtures"


class GoldItem(BaseModel):
    key: str
    must_mention: list[str | list[str]]
    kind: str | None = None


class Trap(BaseModel):
    type: Literal["injection", "planted_number", "contradiction", "gap"]
    note: str = ""
    marker: str | None = None
    forbidden_outputs: list[str] = Field(default_factory=list)
    value: str | None = None
    lines: list[int] = Field(default_factory=list)
    must_be_open: list[str | list[str]] = Field(default_factory=list)


class Gold(BaseModel):
    requirements: list[GoldItem] = Field(default_factory=list)
    open_items: list[GoldItem] = Field(default_factory=list)
    traps: list[Trap] = Field(default_factory=list)


class FollowUpScenario(BaseModel):
    open_item_key: str
    real_answer: str
    non_answer: str = "We do not know yet, we will have to check."


class Fixture(BaseModel):
    id: str
    organization: str
    industry: str
    synthetic: bool = True
    seed: bool = False
    transcript: str
    gold: Gold = Field(default_factory=Gold)
    follow_up: FollowUpScenario | None = None


def load_fixtures(directory: Path | None = None) -> list[Fixture]:
    folder = directory or FIXTURES_DIR
    fixtures = []
    for path in sorted(folder.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        fixtures.append(Fixture.model_validate(data))
    return fixtures
