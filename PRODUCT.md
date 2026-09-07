# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

AI solution engineers, forward-deployed engineers, and technical discovery leads reviewing a customer conversation under time pressure. They need to turn incomplete, messy discovery evidence into a defensible solution brief without losing uncertainty or source attribution.

## Product Purpose

SignalRoom converts a discovery transcript and optional reference material into grounded requirements, open questions, risks, retrieved evidence, and a reviewable solution brief. Success means the reviewer can understand the proposal, inspect why it was made, resolve gaps, and make a recorded human decision in one workspace.

## Positioning

SignalRoom exposes the solutioning process rather than presenting a polished answer as fact: every requirement retains source evidence and confidence, retrieval is visible, gaps remain explicit, a critic pass challenges the proposal, and final approval stays human.

## Operating Context

The primary workflow is: capture a synthetic discovery transcript by text or voice, optionally attach a reference document, run an agent graph, review evidence-backed requirements and retrieved knowledge, answer unresolved questions, re-run the graph, approve or request changes, and export the resulting brief. The portfolio demo must remain useful without external API credentials through deterministic local behavior.

## Capabilities and Constraints

- React and Vite web client with a FastAPI backend.
- LangGraph workflow for discover, structure, retrieve, design, critique, and approve stages.
- Persistent SQLite solution rooms and audit events.
- Embedded Qdrant vector retrieval with deterministic local embeddings.
- Optional live structured-output and audio-transcription adapters.
- Read-only MCP access to knowledge, room, and evaluation tools.
- Human approval is required before finalization.
- All organizations, people, documents, and data shown in the demo are fictional.
- The interface must not imply that synthetic evidence or evaluation values are customer proof.

## Brand Commitments

The product name is SignalRoom. The voice is precise, candid, operational, and calm. It names uncertainty directly, avoids inflated AI language, and treats evidence provenance and human judgment as first-class product behavior.

## Evidence on Hand

- A working end-to-end synthetic demo and deterministic fallback data in `apps/web/src/demo.ts`.
- Backend tests and evaluation fixtures for extraction, grounding, retrieval, review, persistence, and export.
- Architecture and evaluation documentation under `docs/`.
- No customer logos, testimonials, production usage claims, or confidential HawkVision materials may be introduced.

## Product Principles

1. Evidence before recommendation.
2. Uncertainty remains visible until a human resolves it.
3. The next decision should be obvious within seconds.
4. Agent activity is inspectable, not theatrical.
5. The portfolio demo works locally without secrets and never exposes proprietary material.

## Accessibility & Inclusion

The responsive web interface must support keyboard navigation, visible focus, readable text and contrast, reduced motion, and clear status communication without relying on color alone.
