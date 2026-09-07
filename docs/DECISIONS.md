# Engineering decisions

## 2026-09-06 — Local-first evaluation until credentials are rotated

SignalRoom will continue to run its deterministic local path and checked-in fixtures without provider
credentials. No live-model recordings or paid calls are made with a key exposed in chat history.

## 2026-09-06 — Review is a hard API boundary

An approval is only accepted when a session is at the `approval` stage. A reviewer who requests changes
returns the session to `critique`; new evidence must trigger follow-up analysis before another decision.
This prevents the UI from representing an unrecorded or stale approval as a completed decision.
Approved rooms are immutable, so later evidence must be captured in a new discovery room rather than
silently altering the recorded decision.

## 2026-09-06 — Portfolio claims follow executed evidence

Documentation reports the current ten API tests and three deterministic evaluation fixtures. It does not
claim a larger suite, recorded live-model runs, native LangGraph interrupts, FTS5, or fully verified
contradiction detection because those are not present in this working tree.
