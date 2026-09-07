# Evaluation contract

The portfolio claim is not “the agent writes attractive documents.” The measurable claim is that it
turns discovery evidence into a reviewable brief without crossing evidence or approval boundaries.

## V1 metrics

| Dimension | Measurement |
|---|---|
| Requirement recall | Expected requirements recovered from a labeled discovery fixture |
| Grounding | Requirements whose evidence points to an actual source utterance |
| Unsupported claims | Final claims with neither discovery nor retrieved evidence |
| Open-question recall | Known missing facts preserved as questions |
| Approval compliance | Final brief cannot become approved without explicit human action |
| Stage determinism | Same fixture produces the same workflow stage outputs |

## Initial acceptance thresholds

- 100% of displayed requirements have evidence.
- Zero unsupported numeric claims.
- 100% of known missing facts remain visible.
- Zero final approvals without the review endpoint.

## Current deterministic run

The checked-in harness currently exercises three labeled synthetic fixtures: integration + alert +
metric, audit-only, and an underspecified outcome. Its latest local run recovered every expected
requirement with mean precision, recall, and grounding of `1.0`.

This is a regression harness, not a claim of general model performance. It does not yet measure live
model quality, prompt-injection resistance, contradiction handling, latency, cost, or speech accuracy.
Those remain the next evaluation work after a rotated provider key is configured.
