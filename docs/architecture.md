# Architecture

## Product boundary

SignalRoom begins after a customer has agreed to a discovery session and ends at an approved
solution brief. It does not send messages, commit commercial terms, or deploy systems.

## Workflow

```text
discovery input
      |
      v
  discover -----> missing context? -----> open questions
      |
      v
  structure ----> requirements + constraints + success metrics
      |
      v
  retrieve -----> cited capability and pattern evidence
      |
      v
  design --------> architecture + phased PoC plan
      |
      v
  critique ------> contradictions + risks + unsupported claims
      |
      v
  approval ------> human accepts/rejects proposed brief
```

The API uses LangGraph because the workflow has durable state, an explicit review boundary, and
nodes that can be evaluated independently. A review decision is accepted only while the session is at
the approval stage; requesting changes sends it back to critique and requires a follow-up re-analysis
before it can be approved. V1 retrieval uses Qdrant embedded mode and deterministic
hashing embeddings, so the vector-search path is real while remaining reproducible without credentials.
Provider-quality embeddings and an LLM structured-output adapter are the next replaceable components.

## Trust model

- Every requirement retains its supporting evidence.
- Missing facts remain open questions; the system does not silently fill them.
- Retrieved material is distinguished from customer statements.
- A critique stage runs before approval.
- Finalization is a human decision; approved rooms are immutable and require a new discovery room for changes.
- All included data is synthetic.

## Production path

Completed locally: persistent solution rooms and audit events, embedded Qdrant retrieval, PDF/DOCX/
Markdown/text ingestion, visible citations, follow-up re-analysis, review-decision enforcement, DOCX
export, an optional structured-output model adapter, optional recorded-audio transcription, and a
read-only MCP tool surface.

Remaining production path:

1. Streaming speech with partial transcripts, VAD, and interruption handling.
2. Postgres/pgvector deployment plus hybrid retrieval and reranking.
3. Native resumable LangGraph interrupts for the human-review gate. The current SQLite checkpointer
   stores graph state and history, but review orchestration remains an API-level boundary.
4. Trace storage, batch evaluation runs, cost/latency metrics, authentication, and access control.
