"""Deterministic transcript segmentation.

The discover stage does not call a model. It turns raw transcript text into
numbered, speaker-attributed utterances so that every later claim can point
at a line and every quote can be checked against that line in code.
"""

import re
from collections import Counter

from .models import SpeakerCount, Utterance

UNATTRIBUTED = "Unattributed"

# Optional leading timestamp such as "04:18", "[00:04:18]" or "(4:18)", then
# "Speaker name: text". Speaker names are short and contain no sentence
# punctuation, which keeps "Note: the gateway stays" from becoming a speaker
# only when the label looks like a role or a name.
_LINE = re.compile(
    r"^\s*(?:[\[(]?\d{1,2}:\d{2}(?::\d{2})?[\])]?\s*[-–]?\s*)?"
    r"(?P<speaker>[A-Za-z][A-Za-z0-9 .'&/()-]{0,48}?)\s*:\s*(?P<text>\S.*)$"
)

_NON_SPEAKER_LABELS = {"note", "notes", "action", "actions", "summary", "agenda", "decision", "todo", "http", "https"}


def segment(transcript: str, origin: str = "transcript", start_line: int = 1) -> list[Utterance]:
    utterances: list[Utterance] = []
    line_number = start_line
    for raw in transcript.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        match = _LINE.match(stripped)
        if match and match.group("speaker").strip().lower() not in _NON_SPEAKER_LABELS:
            speaker = re.sub(r"\s+", " ", match.group("speaker")).strip()
            text = match.group("text").strip()
        else:
            speaker, text = UNATTRIBUTED, stripped
        utterances.append(Utterance(line=line_number, speaker=speaker, text=text, origin=origin))  # type: ignore[arg-type]
        line_number += 1
    return utterances


def speakers(utterances: list[Utterance]) -> list[SpeakerCount]:
    counts = Counter(item.speaker for item in utterances)
    return [SpeakerCount(speaker=name, lines=count) for name, count in counts.most_common()]


def numbered(utterances: list[Utterance]) -> str:
    """Render utterances the way the model sees them: one line each, zero-padded line tags."""
    width = max(2, len(str(utterances[-1].line))) if utterances else 2
    return "\n".join(f"[L{item.line:0{width}d}] {item.speaker}: {item.text}" for item in utterances)
