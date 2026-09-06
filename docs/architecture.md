# Architecture

## Boundary

SignalRoom starts when a discovery transcript exists and ends when a solution engineer approves a brief. It does not join calls, send messages, price anything, or deploy anything. Every organization, person, document and number in it is invented.

## Shape

```text
apps/web (React, Vite)                      apps/api (FastAPI)
┌──────────────────────────┐   HTTP/JSON    ┌──────────────────────────────────────────────┐
│ rooms · composer · docket│ ─────────────► │ main.py        routes, error mapping, seeding │
│ decision panel · trace   │ ◄───────────── │ workflow.py    LangGraph graph + interrupt    │
└──────────────────────────┘                │ grounding.py   code gates on model output     │
                                            │ model_client.py OpenAI-compatible, record/replay│
                                            │ retrieval.py   SQLite FTS5 pattern library    │
                                            │ persistence.py rooms + audit log (SQLite)     │
                                            │ exports.py     DOCX brief                     │
                                            │ mcp_server.py  read-only MCP tools            │
                                            └──────────────────────────────────────────────┘
                                                     │                    │
                                              recordings/*.json    evals/ fixtures, run.py, results
```

## Workflow

```text
transcript
   │
   ▼
discover   deterministic: numbered, speaker-attributed utterances (no model)
   │
   ▼
extract    model → requirements, use cases, open items, contradictions
   │        code → quote must be a verbatim substring of the cited line;
   │               repaired if found elsewhere, dropped otherwise; speaker from transcript
   ▼
retrieve   FTS5 per requirement and use case → passages with stable ids
   │
   ▼
design     model → SAS-style brief (snapshot, readiness, constraints, phases,
   │               success measures, risks, more open items)
   │        code → strip citations to passages not retrieved; classify every
   │               number: customer said it / reference material / nowhere
   ▼
critique   model → findings and verdict
   │        code → merge: dropped evidence, unverified numbers, invalid citations,
   │               unaddressed contradictions, missing owners
   ▼
gate       LangGraph interrupt. Human decision resumes the thread:
             approve          → END
             request changes  → design (with the note)
             follow-up answers→ extract (answers become new attributed lines;
                                a non-answer cannot close an item)
```

State is checkpointed in SQLite after every node, so a room survives a restart and the trace endpoint shows real steps. The API projects graph state into a `Room` and stores that alongside an audit log of decisions.

## Trust model

- The model proposes. Code decides what survives. Every gate records what it changed.
- Transcript and reference text reach the model inside delimiters described as data. The real defence is that outputs are schema-constrained and checked, not the instruction.
- Numbers the customer did not say are flagged by provenance, not silently accepted.
- Approval is an interrupt in the workflow, not a status flag. It is not exposed through MCP.
- Without a key the app opens recorded rooms and says plainly that new transcripts need a key.

## Model calls

One function, `structured_call`, sends a system and user message to an OpenAI-compatible endpoint with strict JSON schema output and returns a validated Pydantic object plus latency, tokens and an estimated cost. Calls are keyed by a content hash and can be recorded and replayed; see `docs/DECISIONS.md`.

## Evaluation

`apps/api/evals/run.py` runs the ten fixtures through the real graph, scores them against gold labels and planted traps, exercises the follow-up gate, and writes results to `evals/results/latest.json` and `docs/evaluation.md`. CI replays committed recordings so the numbers are reproducible without a key.

## Not built, on purpose

Streaming stage updates in the UI, Postgres, authentication, multi-tenant rooms, hosted deployment. Each is a known next step, none is needed to prove the claim.
