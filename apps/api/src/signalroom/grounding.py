"""Code-enforced checks on model output.

The model proposes; this module decides what survives. Three families:

- `ground_extraction`: every requirement and use case must point at a real
  line and quote a verbatim substring of that line. A quote that exists on a
  different line is repaired and the repair is recorded. Anything else is
  dropped and the drop is recorded. The speaker always comes from the
  transcript, never from the model.
- `check_brief`: citations must refer to retrieved passages that exist, and
  numbers in the brief must be traceable to the transcript (grounded), to a
  retrieved passage (pattern-derived, flagged), or to nothing (flagged high).
- `is_real_answer`: a follow-up answer that says "we don't know" cannot close
  an open item, whatever the model concluded.
"""

import re
from collections import defaultdict
from collections.abc import Iterable

from .models import (
    Brief,
    BriefDraft,
    Contradiction,
    Extraction,
    Evidence,
    Finding,
    GroundingDrop,
    GroundingRepair,
    GroundingReport,
    OpenItem,
    ProposedEvidence,
    Requirement,
    SearchHit,
    UseCase,
    Utterance,
)


_UNICODE_PUNCTUATION = str.maketrans({
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-",
    " ": " ", " ": " ", " ": " ",
})


def ascii_punctuation(text: str) -> str:
    """Models emit non-breaking hyphens and narrow spaces; fold them so regexes and substring checks behave."""
    return text.translate(_UNICODE_PUNCTUATION)


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", ascii_punctuation(text)).strip().lower()


_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000, "dozen": 12,
}
_TENS = {"twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"}
_NUMBER_WORD = re.compile(r"\b(" + "|".join(_NUMBER_WORDS) + r")(?:[\s-](one|two|three|four|five|six|seven|eight|nine))?\b", re.IGNORECASE)


def number_words_to_digits(text: str) -> str:
    """'thirty days' -> '30 days', 'twenty-five' -> '25', 'a dozen' -> '12'. Used only to build the set of numbers a speaker actually said."""
    def replace(match: re.Match) -> str:
        first = _NUMBER_WORDS[match.group(1).lower()]
        second = match.group(2)
        if second and match.group(1).lower() in _TENS:
            return str(first + _NUMBER_WORDS[second.lower()])
        return str(first) + (f" {second}" if second else "")
    return _NUMBER_WORD.sub(replace, ascii_punctuation(text))


def _content_terms(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", _normalise(text)) if len(token) >= 4 and token not in _QUESTION_STOPWORDS}


_QUESTION_STOPWORDS = {"what", "which", "when", "where", "will", "does", "have", "with", "that", "this", "from", "into", "there",
                       "their", "about", "should", "would", "could", "exact", "exactly", "confirm", "confirmation", "details", "detail"}


def similar_questions(a: str, b: str, threshold: float = 0.6) -> bool:
    """Two open items are the same question when the shorter one's content terms mostly appear in the other.

    Overlap coefficient rather than Jaccard, so "API rate-limit details" and
    "API rate-limit details (calls per minute/second)" count as one question.
    """
    terms_a, terms_b = _content_terms(a), _content_terms(b)
    smallest = min(len(terms_a), len(terms_b))
    if smallest < 2:
        return _normalise(a) == _normalise(b)
    return len(terms_a & terms_b) / smallest >= threshold


def locate_quote(evidence: ProposedEvidence, utterances: list[Utterance]) -> tuple[Evidence | None, str | None, int | None]:
    """Return (evidence, drop_reason, repaired_from_line).

    Success with no repair: (Evidence, None, None). Success after relocating the
    quote to the line it actually appears on: (Evidence, None, proposed_line).
    Failure: (None, reason, None).
    """
    by_line = {item.line: item for item in utterances}
    quote = _normalise(evidence.quote)
    if len(quote) < 3:
        return None, "empty_quote", None
    target = by_line.get(evidence.line)
    if target and quote in _normalise(target.text):
        return Evidence(line=target.line, speaker=target.speaker, quote=evidence.quote.strip()), None, None
    for item in utterances:
        if quote in _normalise(item.text):
            return Evidence(line=item.line, speaker=item.speaker, quote=evidence.quote.strip()), None, evidence.line
    if target is None:
        return None, "line_out_of_range", None
    return None, "quote_not_on_line", None


def ground_extraction(
    extraction: Extraction,
    utterances: list[Utterance],
    existing_open_items: list[OpenItem] | None = None,
) -> tuple[list[Requirement], list[UseCase], list[OpenItem], list[Contradiction], GroundingReport]:
    report = GroundingReport()
    requirements: list[Requirement] = []
    use_cases: list[UseCase] = []

    for index, proposed in enumerate(extraction.requirements, start=1):
        report.proposed += 1
        evidence, reason, repaired_from = locate_quote(proposed.evidence, utterances)
        if evidence is None:
            report.dropped += 1
            report.drops.append(GroundingDrop(
                kind="requirement", title=proposed.title, reason=reason or "quote_not_in_transcript",
                proposed_line=proposed.evidence.line, proposed_quote=proposed.evidence.quote,
            ))
            continue
        if repaired_from is not None:
            report.repaired += 1
            report.repairs.append(GroundingRepair(kind="requirement", title=proposed.title, proposed_line=repaired_from, actual_line=evidence.line))
        report.passed += 1
        requirements.append(Requirement(
            id=f"REQ-{len(requirements) + 1:02d}", title=proposed.title, detail=proposed.detail, kind=proposed.kind,
            confidence=proposed.confidence, confidence_reason=proposed.confidence_reason, evidence=evidence,
        ))

    for proposed_case in extraction.use_cases:
        report.proposed += 1
        evidence, reason, repaired_from = locate_quote(proposed_case.evidence, utterances)
        if evidence is None:
            report.dropped += 1
            report.drops.append(GroundingDrop(
                kind="use_case", title=proposed_case.name, reason=reason or "quote_not_in_transcript",
                proposed_line=proposed_case.evidence.line, proposed_quote=proposed_case.evidence.quote,
            ))
            continue
        if repaired_from is not None:
            report.repaired += 1
            report.repairs.append(GroundingRepair(kind="use_case", title=proposed_case.name, proposed_line=repaired_from, actual_line=evidence.line))
        report.passed += 1
        use_cases.append(UseCase(
            id=f"UC-{len(use_cases) + 1:02d}", name=proposed_case.name, trigger_condition=proposed_case.trigger_condition,
            expected_output=proposed_case.expected_output, evidence=evidence,
        ))

    valid_lines = {item.line for item in utterances}
    open_items = merge_open_items(extraction, utterances, existing_open_items or [], valid_lines)

    contradictions = [
        Contradiction(topic=item.topic, line_a=item.line_a, line_b=item.line_b, note=item.note)
        for item in extraction.contradictions
        if item.line_a in valid_lines and item.line_b in valid_lines and item.line_a != item.line_b
    ]
    return requirements, use_cases, open_items, contradictions, report


NON_ANSWER = re.compile(
    r"(don'?t know|do not know|not sure|unsure|unknown|no idea|tbc|to be confirmed|will (check|confirm|find out|get back)|"
    r"need to (check|confirm|ask)|can'?t say|cannot say|not certain|\?\s*$)",
    re.IGNORECASE,
)


def is_real_answer(answer: str) -> bool:
    text = answer.strip()
    if len(text) < 8:
        return False
    return NON_ANSWER.search(text) is None


def merge_open_items(
    extraction: Extraction,
    utterances: list[Utterance],
    existing: list[OpenItem],
    valid_lines: set[int],
) -> list[OpenItem]:
    """Carry answered items forward, apply verified resolutions, then add new items.

    A resolution is accepted only when it names an existing open item, points at a
    follow-up line that exists, and that line holds a real answer.
    """
    by_line = {item.line: item for item in utterances}
    result: list[OpenItem] = []
    resolved_ids: set[str] = set()
    resolutions = {item.open_item_id: item for item in extraction.resolutions}

    for item in existing:
        carried = item.model_copy(deep=True)
        if carried.status == "answered":
            result.append(carried)
            continue
        resolution = resolutions.get(carried.id)
        if resolution:
            line = by_line.get(resolution.resolved_by_line)
            if line and line.origin == "follow_up" and is_real_answer(_answer_text(line.text)):
                carried.status = "answered"
                carried.answer = _answer_text(line.text)
                carried.answered_line = line.line
                resolved_ids.add(carried.id)
            result.append(carried)
        else:
            result.append(carried)

    next_index = len(result) + 1
    for proposed in extraction.open_items:
        if any(similar_questions(proposed.question, existing_item.question) for existing_item in result):
            continue
        related = proposed.related_line if proposed.related_line in valid_lines else None
        result.append(OpenItem(
            id=f"OI-{next_index:02d}", question=proposed.question, why_it_matters=proposed.why_it_matters,
            suggested_owner_role=proposed.suggested_owner_role or "Unassigned", related_line=related,
        ))
        next_index += 1
    return result


def _answer_text(text: str) -> str:
    """Follow-up lines are rendered as 'Answer to OI-03 (question): answer'. Return the answer part."""
    marker = "): "
    return text.split(marker, 1)[1] if marker in text else text


# ----------------------------------------------------------------------------
# Brief checks
# ----------------------------------------------------------------------------

_ID_TOKENS = re.compile(r"\b(?:REQ|UC|OI|L)-?\d+\b", re.IGNORECASE)
# Passages are cited as "<slug>#<n>" (see retrieval.py); the n is an index into the library, not a claim.
_PASSAGE_CITATION = re.compile(r"\b[a-z0-9][a-z0-9-]*#\d+", re.IGNORECASE)
_NUMBER = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?\s?%?)(?![\w.])")
_ORDINAL_CONTEXT = re.compile(r"\b(?:phase|step|option|stage|tier|priority|q)\s*$", re.IGNORECASE)


def numbers_in(text: str, passage_ids: Iterable[str] = ()) -> list[str]:
    """Numbers stated in the text, ignoring requirement/line ids, phase ordinals and passage citations.

    `passage_ids` are removed verbatim first, so a retrieved id that does not fit the slug shape is still not read as a number.
    """
    cleaned = ascii_punctuation(text)
    exact = sorted({ascii_punctuation(pid) for pid in passage_ids if pid}, key=len, reverse=True)
    if exact:
        cleaned = re.sub("(?:" + "|".join(map(re.escape, exact)) + r")(?!\d)", " ", cleaned, flags=re.IGNORECASE)
    cleaned = _ID_TOKENS.sub(" ", _PASSAGE_CITATION.sub(" ", cleaned))
    found: list[str] = []
    for match in _NUMBER.finditer(cleaned):
        token = match.group(1).replace(" ", "")
        prefix = cleaned[: match.start()]
        if token.isdigit() and len(token) == 1 and _ORDINAL_CONTEXT.search(prefix):
            continue
        found.append(token)
    return found


def _brief_text_fields(brief: BriefDraft | Brief) -> list[tuple[str, str]]:
    """Locations are paths into the brief JSON, so list indexes count from zero."""
    fields: list[tuple[str, str]] = [
        ("snapshot.one_line_goal", brief.snapshot.one_line_goal),
        ("snapshot.scope_summary", brief.snapshot.scope_summary),
        ("snapshot.deployment_shape", brief.snapshot.deployment_shape),
        ("recommendation.approach", brief.recommendation.approach),
    ]
    for index, phase in enumerate(brief.recommendation.phases):
        fields.append((f"recommendation.phases[{index}].duration", phase.duration))
        fields.append((f"recommendation.phases[{index}].purpose", phase.purpose))
        for criterion in phase.exit_criteria:
            fields.append((f"recommendation.phases[{index}].exit_criteria", criterion))
    for index, item in enumerate(brief.constraints):
        fields.append((f"constraints[{index}]", item.constraint))
    for index, item in enumerate(brief.success_measures):
        fields.append((f"success_measures[{index}]", item.measure))
    for index, item in enumerate(brief.risks):
        fields.append((f"risks[{index}].mitigation", item.mitigation))
        fields.append((f"risks[{index}].basis", item.basis))
    for index, item in enumerate(brief.readiness):
        fields.append((f"readiness[{index}].note", item.note))
    return fields


def check_brief(draft: BriefDraft, utterances: list[Utterance], retrieved: list[SearchHit]) -> tuple[BriefDraft, list[Finding]]:
    """Strip invalid citations and flag numbers. Returns the cleaned draft and code findings."""
    findings: list[Finding] = []
    known_passages = {hit.passage_id for hit in retrieved}
    transcript_numbers = set()
    for item in utterances:
        transcript_numbers.update(numbers_in(number_words_to_digits(item.text)))
    passage_numbers: dict[str, list[str]] = defaultdict(list)
    for hit in retrieved:
        for number in numbers_in(number_words_to_digits(hit.passage)):
            passage_numbers[number].append(hit.passage_id)

    for assessment in draft.readiness:
        invalid = [pid for pid in assessment.cited_passage_ids if pid not in known_passages]
        if invalid:
            assessment.cited_passage_ids = [pid for pid in assessment.cited_passage_ids if pid in known_passages]
            findings.append(Finding(
                kind="invalid_citation", severity="medium", source="code",
                text=f"Readiness note for {assessment.use_case_id} cited passages that were not retrieved: {', '.join(invalid)}. The citations were removed.",
                location=f"readiness.{assessment.use_case_id}",
            ))
        if assessment.readiness == "proven_pattern" and not assessment.cited_passage_ids:
            assessment.readiness = "unknown"
            findings.append(Finding(
                kind="overclaim", severity="medium", source="code",
                text=f"{assessment.use_case_id} was marked a proven pattern without any retrieved passage to support it. Downgraded to unknown.",
                location=f"readiness.{assessment.use_case_id}",
            ))

    for constraint in draft.constraints:
        if constraint.passage_id and constraint.passage_id not in known_passages:
            findings.append(Finding(
                kind="invalid_citation", severity="low", source="code",
                text=f"Constraint cited a passage that was not retrieved: {constraint.passage_id}.",
                location="constraints",
            ))
            constraint.passage_id = None

    # One finding per brief field: which numbers came from reference material and which from nowhere.
    per_location: dict[str, tuple[list[str], list[str]]] = {}
    for location, text in _brief_text_fields(draft):
        for number in numbers_in(text, known_passages):
            if number in transcript_numbers:
                continue
            from_reference, from_nowhere = per_location.setdefault(location, ([], []))
            bucket = from_reference if number in passage_numbers else from_nowhere
            if number not in bucket:
                bucket.append(number)
    for location, (from_reference, from_nowhere) in per_location.items():
        parts = []
        if from_nowhere:
            parts.append(f"{', '.join(repr(n) for n in from_nowhere)} appear{'s' if len(from_nowhere) == 1 else ''} nowhere in the conversation or the retrieved passages")
        if from_reference:
            sources = sorted({pid for n in from_reference for pid in passage_numbers[n][:2]})
            parts.append(f"{', '.join(repr(n) for n in from_reference)} come{'s' if len(from_reference) == 1 else ''} from reference material ({', '.join(sources)}), not from the customer")
        findings.append(Finding(
            kind="unverified_number", severity="high" if from_nowhere else "medium", source="code", location=location,
            text=f"In {location}: " + "; ".join(parts) + ". Numbers the customer did not state belong in TBC or as pattern guidance, not as facts.",
        ))
    return draft, findings
