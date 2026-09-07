from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader


SUPPORTED = {".txt", ".md", ".pdf", ".docx"}


async def extract_text(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError("Supported formats: TXT, Markdown, PDF, and DOCX")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise ValueError("Document exceeds the 10 MB limit")
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="replace")
    if suffix == ".pdf":
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
    document = Document(BytesIO(content))
    return "\n\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
