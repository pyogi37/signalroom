import os
from io import BytesIO


def transcription_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def transcribe_audio(content: bytes, filename: str) -> str:
    if not transcription_enabled():
        raise RuntimeError("Voice transcription requires OPENAI_API_KEY")
    from openai import OpenAI

    audio = BytesIO(content)
    audio.name = filename
    result = OpenAI().audio.transcriptions.create(
        model=os.getenv("SIGNALROOM_TRANSCRIBE_MODEL", "gpt-transcribe"),
        file=audio,
        response_format="text",
    )
    return str(result)
