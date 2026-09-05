import re

from .models import Session


def evaluate(session: Session) -> dict[str, int | float | bool | str]:
    grounded = sum(1 for item in session.requirements if item.evidence.quote.strip())
    numeric_claims = re.findall(r"\b\d+(?:\.\d+)?%?\b", str(session.brief.get("recommendation", "")))
    return {
        "requirements": len(session.requirements),
        "grounded_requirements": grounded,
        "grounding_rate": round(grounded / len(session.requirements), 3) if session.requirements else 0,
        "unsupported_numeric_claims": len(numeric_claims),
        "open_questions": len(session.open_questions),
        "retrieval_hits": len(session.brief.get("retrieval", [])),
        "approval_required": True,
        "execution_mode": str(session.brief.get("execution_mode", "demo fixture")),
    }
