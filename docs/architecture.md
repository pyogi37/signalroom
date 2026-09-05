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

The API uses LangGraph because the workflow has durable state, conditional review boundaries, and
nodes that can be evaluated independently. V1 retrieval uses Qdrant embedded mode and deterministic
hashing embeddings, so the vector-search path is real while remaining reproducible without credentials.
Provider-quality embeddings and an LLM structured-output adapter are the next replaceable components.

## Trust model

- Every requirement retains its supporting evidence.
- Missing facts remain open questions; the system does not silently fill them.
- Retrieved material is distinguished from customer statements.
- A critique stage runs before approval.
- Finalization is a human decision.
- All included data is synthetic.

## Production path

Completed locally: persistent solution rooms and audit events, embedded Qdrant retrieval, PDF/DOCX/
Markdown/text ingestion, visible citations, follow-up re-analysis, DOCX export, an optional structured-
output model adapter, optional recorded-audio transcription, and a read-only MCP tool surface.

Remaining production path:

1. Streaming speech with partial transcripts, VAD, and interruption handling.
2. Postgres/pgvector deployment plus hybrid retrieval and reranking.
3. Persistent LangGraph checkpointers and native resumable interrupts.
4. Trace storage, batch evaluation runs, cost/latency metrics, authentication, and access control.
