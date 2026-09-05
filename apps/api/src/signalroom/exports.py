from io import BytesIO

from docx import Document

from .models import Session


def brief_docx(session: Session) -> BytesIO:
    document = Document()
    document.add_heading("SignalRoom Solution Brief", 0)
    document.add_paragraph(f"Organization: {session.organization}")
    document.add_paragraph(f"Status: {session.status.upper()}")
    document.add_heading("Problem", level=1)
    document.add_paragraph(str(session.brief.get("problem", "")))
    document.add_heading("Recommendation", level=1)
    document.add_paragraph(str(session.brief.get("recommendation", "")))
    document.add_heading("Evidence-backed requirements", level=1)
    for item in session.requirements:
        document.add_heading(f"{item.id} — {item.title}", level=2)
        document.add_paragraph(item.detail)
        document.add_paragraph(f'Evidence ({item.evidence.speaker}): “{item.evidence.quote}”')
    document.add_heading("Proposed architecture", level=1)
    for item in session.brief.get("architecture", []):
        document.add_paragraph(str(item), style="List Bullet")
    document.add_heading("Risks", level=1)
    for risk in session.risks:
        document.add_paragraph(f"{risk.title} ({risk.severity}): {risk.mitigation}", style="List Bullet")
    document.add_heading("Open questions", level=1)
    for question in session.open_questions:
        document.add_paragraph(question, style="List Bullet")
    document.add_paragraph("AI-generated working material. Human review is required before use.")
    output = BytesIO()
    document.save(output)
    output.seek(0)
    return output
