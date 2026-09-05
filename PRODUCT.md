# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

AI solution engineers, forward-deployed engineers, and technical discovery leads who have just come out of a customer discovery call and need a defensible first-cut solution brief before the next conversation. They work under time pressure, they are held to what the brief says, and they know from experience that a confident paragraph with no source is a liability. They want to see where every claim came from, what is still unknown, and who has to answer it.

Secondary audience: technical hiring leads evaluating this project as portfolio evidence. They read the code and the eval results, not the pitch.

## Product Purpose

SignalRoom turns a discovery transcript into a grounded solution brief. It segments the conversation, extracts requirements and use cases with exact quoted evidence, retrieves matching patterns from a small reference library, drafts a brief in the working shape of a Solution Architecture Spec, runs a critic pass against the transcript, and stops at a human gate. Success means a reviewer can see why every line of the brief exists, what the model was not allowed to claim, and make a recorded decision: approve, send back, or add answers and re-run.

The portfolio claim is narrow and measurable: the brief never says something the conversation did not, and when it cannot support a claim it says so instead of guessing.

## Positioning

Every requirement in the brief carries a quote that code has verified is an exact substring of a numbered transcript line, attributed to the speaker who said it. Anything the model proposes that fails that check is dropped and the drop is shown, not hidden. A second model pass reads the brief against the transcript and flags unsupported numbers, contradictions between speakers, and missing owners. An evaluation suite over labelled synthetic transcripts with planted traps reports recall, precision, grounding, trap pass rate, latency and token cost, and its failures are published alongside its scores. Approval is a real interrupt in the workflow, not a status flag.

## Operating Context

The primary workflow: paste or upload a discovery transcript (text; the kind that comes out of a recorded call), optionally add a synthetic reference document to the pattern library, run the workflow, review the brief section by section with its evidence, read the critic findings, then either approve, request changes with a note, or answer open items and re-run. Approved briefs export to DOCX.

The model runs through an OpenAI-compatible endpoint, Groq by default, with the key supplied in a local `.env`. Without a key the app opens the bundled synthetic rooms with their recorded model outputs, traces and evaluation results, and says plainly that analysing a new transcript needs a key. Continuous integration runs the evaluation suite from those same recordings so results are reproducible and free.

Vocabulary borrowed from solutioning practice: use case, trigger condition, expected output, readiness, constraint, open item, owner, TBC, baseline, exit criteria. None of it is tied to any real engagement.

## Capabilities and Constraints

- React and Vite client, FastAPI backend, LangGraph workflow with a SQLite checkpointer.
- Workflow stages: discover (deterministic segmentation into numbered, speaker-attributed utterances), extract (model, structured output), retrieve (SQLite full-text search over a synthetic pattern library), design (model, SAS-style brief), critique (model plus code checks), gate (human interrupt).
- Code-enforced grounding: line reference must exist, quote must be an exact substring of that line, speaker comes from the transcript, never from the model. Repairs and drops are recorded per run.
- Brief sections: snapshot, use cases with trigger conditions and expected outputs, readiness and feasibility notes, environment and constraints, recommendation with phases and exit criteria, success measures with baseline status, risks, open items with suggested owner roles.
- Gate decisions: approve, request changes with a note (returns to design), add answers to open items (returns to extract with the answers as new attributed utterances). All three are recorded in an audit log.
- Recorded model responses: every model call can be recorded and replayed by content hash. Modes are live, replay, record, and auto.
- Per-run metrics: model, mode, latency and token usage per stage, estimated cost using a configurable price table.
- Evaluation suite: labelled synthetic transcripts with gold requirements, gold open items and planted traps (injection lines, planted numbers, speaker contradictions, deliberate gaps).
- Read-only MCP tools over knowledge search, room state and evaluation results. Approval is never exposed through MCP.
- DOCX export of the brief.
- Synthetic data constraint: every organization, person, site, document, number and transcript in this repository is invented and labelled as such. Nothing may be derived from any real customer, prospect or engagement. This is a product rule, not a disclaimer.
- The interface must never present synthetic evidence or evaluation values as customer proof or production results.
- Undecided: whether a synthetic commercials section is added to the brief later. Pricing and ROI generation are out of scope for now but not ruled out.

## Non-goals

- No voice capture or audio transcription.
- No sending messages, scheduling, or committing commercial terms.
- No pricing or ROI generation in the current scope (see undecided above).
- No customer, prospect or engagement data, ever, including indirectly through examples.
- No production or customer-use claims. This is a portfolio build.
- No multi-tenant authentication or access control.
- Not a CRM, pipeline tracker or note-taking system.
- No streaming speech, no live call joining.

## Brand Commitments

The product name is SignalRoom. The voice is precise, candid, operational and calm. It names uncertainty directly, avoids inflated AI language, uses no em dashes, and treats evidence provenance and human judgment as first-class product behaviour. Model output is labelled as working material until a human approves it.

## Evidence on Hand

- Synthetic discovery transcripts and their gold labels under `apps/api/evals/fixtures/`.
- Recorded model responses under `apps/api/recordings/` that make the demo and the evaluation suite reproducible without a key.
- Evaluation results with numbers, date, model and failures in `docs/evaluation.md`.
- Design decisions and their tradeoffs in `docs/DECISIONS.md`.
- Absent and never to be fabricated: customer logos, testimonials, production usage, real deal or site data, HawkVision materials of any kind.

## Product Principles

1. Evidence before recommendation. A claim without a quoted line is a question, not a requirement.
2. Uncertainty stays visible until a named human resolves it.
3. Show what the model was not allowed to say, not only what it said.
4. Workflow activity is inspectable, not theatrical. Every stage does real work or does not exist.
5. Works locally without secrets through recorded runs, and never exposes proprietary material.
6. The next human decision is obvious within seconds of opening a room.

## Accessibility & Inclusion

The responsive web interface must support keyboard navigation, visible focus, readable text and contrast, reduced motion, and clear status communication without relying on colour alone. Every evidence marker and severity has a text equivalent.
