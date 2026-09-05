from signalroom.grounding import check_brief, ground_extraction, is_real_answer, numbers_in
from signalroom.models import (
    BriefDraft,
    Constraint,
    Extraction,
    OpenItem,
    Phase,
    ProposedContradiction,
    ProposedEvidence,
    ProposedOpenItem,
    ProposedRequirement,
    ProposedResolution,
    ProposedUseCase,
    ReadinessAssessment,
    Recommendation,
    Risk,
    SearchHit,
    Snapshot,
    SuccessMeasure,
)
from signalroom.segmentation import segment

TRANSCRIPT = (
    "Operations lead: We usually discover an excursion when the shift report is already being written.\n"
    "IT architect: The gateway is staying. Anything new has to consume its API.\n"
    "Sponsor: A supervisor can lose most of an hour piecing together one event.\n"
    "IT architect: Actually we might replace the gateway next year.\n"
)
UTTERANCES = segment(TRANSCRIPT)


def requirement(title, line, quote, kind="functional"):
    return ProposedRequirement(title=title, detail=title, kind=kind, evidence=ProposedEvidence(line=line, quote=quote),
                               confidence="high", confidence_reason="explicit")


def test_exact_quote_on_the_right_line_passes_and_speaker_comes_from_transcript():
    extraction = Extraction(
        requirements=[requirement("Detect excursions", 1, "discover an excursion when the shift report")],
        use_cases=[], open_items=[], contradictions=[], resolutions=[],
    )
    reqs, cases, items, contradictions, report = ground_extraction(extraction, UTTERANCES)
    assert [item.id for item in reqs] == ["REQ-01"]
    assert reqs[0].evidence.speaker == "Operations lead"
    assert (report.proposed, report.passed, report.repaired, report.dropped) == (1, 1, 0, 0)


def test_quote_on_another_line_is_repaired_and_recorded():
    extraction = Extraction(
        requirements=[requirement("Use existing gateway", 3, "Anything new has to consume its API", kind="constraint")],
        use_cases=[], open_items=[], contradictions=[], resolutions=[],
    )
    reqs, _, _, _, report = ground_extraction(extraction, UTTERANCES)
    assert reqs[0].evidence.line == 2 and reqs[0].evidence.speaker == "IT architect"
    assert report.repaired == 1 and report.repairs[0].proposed_line == 3 and report.repairs[0].actual_line == 2


def test_invented_quote_is_dropped_and_recorded():
    extraction = Extraction(
        requirements=[requirement("Cut investigation time by 40%", 3, "reduce investigation time by 40%", kind="success_measure")],
        use_cases=[ProposedUseCase(name="Door left open", trigger_condition="door open > 5 min", expected_output="alert",
                                   evidence=ProposedEvidence(line=9, quote="door"))],
        open_items=[], contradictions=[], resolutions=[],
    )
    reqs, cases, _, _, report = ground_extraction(extraction, UTTERANCES)
    assert reqs == [] and cases == []
    assert report.dropped == 2
    assert {drop.reason for drop in report.drops} == {"quote_not_on_line", "line_out_of_range"}


def test_quotes_are_matched_ignoring_whitespace_and_curly_quotes():
    extraction = Extraction(
        requirements=[requirement("Hour lost", 3, "lose  most of an hour")],
        use_cases=[], open_items=[], contradictions=[], resolutions=[],
    )
    reqs, _, _, _, report = ground_extraction(extraction, UTTERANCES)
    assert report.passed == 1 and reqs[0].evidence.line == 3


def test_contradictions_need_two_distinct_real_lines():
    extraction = Extraction(
        requirements=[], use_cases=[], open_items=[], resolutions=[],
        contradictions=[
            ProposedContradiction(topic="Gateway future", line_a=2, line_b=4, note="stays vs replaced"),
            ProposedContradiction(topic="bogus", line_a=2, line_b=2, note="same line"),
            ProposedContradiction(topic="bogus", line_a=2, line_b=40, note="missing line"),
        ],
    )
    _, _, _, contradictions, _ = ground_extraction(extraction, UTTERANCES)
    assert [item.topic for item in contradictions] == ["Gateway future"]


def test_open_items_get_ids_owner_defaults_and_dedupe():
    extraction = Extraction(
        requirements=[], use_cases=[], contradictions=[], resolutions=[],
        open_items=[
            ProposedOpenItem(question="What baseline exists?", why_it_matters="metric", suggested_owner_role="", related_line=3),
            ProposedOpenItem(question="what baseline exists?", why_it_matters="dup", suggested_owner_role="Sponsor", related_line=99),
        ],
    )
    _, _, items, _, _ = ground_extraction(extraction, UTTERANCES)
    assert len(items) == 1
    assert items[0].id == "OI-01" and items[0].suggested_owner_role == "Unassigned" and items[0].related_line == 3


def test_non_answers_cannot_close_an_item_even_if_the_model_says_so():
    existing = [OpenItem(id="OI-01", question="What baseline exists?", why_it_matters="m", suggested_owner_role="Sponsor")]
    follow_up = segment("Follow-up answer: Answer to OI-01 (What baseline exists?): We do not know yet, we will check.", origin="follow_up", start_line=5)
    extraction = Extraction(requirements=[], use_cases=[], open_items=[], contradictions=[],
                            resolutions=[ProposedResolution(open_item_id="OI-01", resolved_by_line=5, note="answered")])
    _, _, items, _, _ = ground_extraction(extraction, UTTERANCES + follow_up, existing)
    assert items[0].status == "open"


def test_real_answer_on_a_follow_up_line_closes_the_item():
    existing = [OpenItem(id="OI-01", question="What baseline exists?", why_it_matters="m", suggested_owner_role="Sponsor")]
    follow_up = segment("Follow-up answer: Answer to OI-01 (What baseline exists?): The shift log from the last two quarters is the baseline.", origin="follow_up", start_line=5)
    extraction = Extraction(requirements=[], use_cases=[], open_items=[], contradictions=[],
                            resolutions=[ProposedResolution(open_item_id="OI-01", resolved_by_line=5, note="answered")])
    _, _, items, _, _ = ground_extraction(extraction, UTTERANCES + follow_up, existing)
    assert items[0].status == "answered" and items[0].answered_line == 5
    assert items[0].answer.startswith("The shift log")


def test_resolution_pointing_at_a_transcript_line_is_ignored():
    existing = [OpenItem(id="OI-01", question="Q?", why_it_matters="m", suggested_owner_role="Sponsor")]
    extraction = Extraction(requirements=[], use_cases=[], open_items=[], contradictions=[],
                            resolutions=[ProposedResolution(open_item_id="OI-01", resolved_by_line=2, note="it was there all along")])
    _, _, items, _, _ = ground_extraction(extraction, UTTERANCES, existing)
    assert items[0].status == "open"


def test_is_real_answer():
    assert is_real_answer("Service accounts with rotating tokens, owned by the platform team.")
    assert not is_real_answer("We don't know yet")
    assert not is_real_answer("TBC")
    assert not is_real_answer("Will confirm with IT next week")
    assert not is_real_answer("Is it OAuth?")
    assert not is_real_answer("yes")


def test_numbers_in_ignores_ids_and_phase_ordinals():
    assert numbers_in("Phase 1 runs on 2 sites for 6 weeks with a 42% target; see REQ-01 and L07 and UC-3") == ["2", "6", "42%"]
    assert numbers_in("Roughly 1.5 hours per event") == ["1.5"]


def draft(**overrides) -> BriefDraft:
    base = dict(
        snapshot=Snapshot(one_line_goal="Detect excursions earlier", scope_summary="Two sites", deployment_shape="TBC", stakeholder_roles=["Operations lead"]),
        readiness=[ReadinessAssessment(use_case_id="UC-01", readiness="proven_pattern", note="pattern", cited_passage_ids=["known#1", "made-up#9"])],
        constraints=[Constraint(constraint="Gateway stays", source="transcript", line=2, passage_id=None),
                     Constraint(constraint="Read-only first", source="pattern_library", line=None, passage_id="nope#1")],
        recommendation=Recommendation(approach="Run a 6 week pilot", phases=[Phase(name="Validate", purpose="check", duration="TBC", exit_criteria=["Alerts fire within 5 minutes"])], discussed_not_in_scope=[]),
        success_measures=[SuccessMeasure(measure="Cut investigation time by 42%", baseline_status="not_stated", owner_role="Sponsor", line=None)],
        risks=[Risk(title="Alert fatigue", severity="medium", mitigation="calibrate", basis="L1")],
        additional_open_items=[],
    )
    base.update(overrides)
    return BriefDraft(**base)


RETRIEVED = [SearchHit(passage_id="known#1", title="Known", passage="Customers typically report a 42% reduction.", score=1.0, source="synthetic vendor sheet")]


def test_check_brief_strips_invalid_citations_and_flags_numbers_by_provenance():
    cleaned, findings = check_brief(draft(), UTTERANCES, RETRIEVED)
    assert cleaned.readiness[0].cited_passage_ids == ["known#1"]
    assert cleaned.constraints[1].passage_id is None
    kinds = {(item.kind, item.severity, item.location) for item in findings}
    assert ("invalid_citation", "medium", "readiness.UC-01") in kinds
    assert ("invalid_citation", "low", "constraints") in kinds
    assert ("unverified_number", "high", "recommendation.approach") in kinds          # 6 weeks: nowhere
    assert ("unverified_number", "high", "recommendation.phases[1].exit_criteria") in kinds  # 5 minutes: nowhere
    assert ("unverified_number", "medium", "success_measures[1]") in kinds          # 42%: from the vendor sheet
    assert all(item.source == "code" for item in findings)


def test_proven_pattern_without_citation_is_downgraded():
    cleaned, findings = check_brief(
        draft(readiness=[ReadinessAssessment(use_case_id="UC-01", readiness="proven_pattern", note="n", cited_passage_ids=[])]),
        UTTERANCES, RETRIEVED,
    )
    assert cleaned.readiness[0].readiness == "unknown"
    assert any(item.kind == "overclaim" for item in findings)


def test_numbers_present_in_transcript_are_not_flagged():
    text = "Sponsor: We run 2 sites and lose about 40 minutes per event."
    utterances = segment(text)
    cleaned, findings = check_brief(
        draft(recommendation=Recommendation(approach="Cover 2 sites; target under 40 minutes", phases=[], discussed_not_in_scope=[]),
              success_measures=[], readiness=[], constraints=[], risks=[]),
        utterances, [],
    )
    assert findings == []
