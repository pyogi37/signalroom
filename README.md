# SignalRoom

A discovery transcript goes in. A solution brief comes out, with every claim tied to a numbered line the customer actually said, a critic pass listing what could not be supported, and a human gate before anything is final.

Everything in this repository is synthetic. The organizations, people, transcripts and reference documents are invented for the demo and labelled as such.

## The problem

After a customer discovery call, a solution engineer has to turn forty minutes of messy conversation into a first-cut brief that a delivery team can act on. The dangerous failure is not a missing requirement. It is a confident sentence nobody said: a duration that was never agreed, a number lifted from a vendor sheet, a "requirement" that was one person thinking aloud while another disagreed. SignalRoom is built around making that failure visible and hard.

## What it does

```text
transcript ─► discover ─► extract ─► retrieve ─► design ─► critique ─► gate ─► approved brief
              (code)      (model +   (FTS5)      (model +   (model +   (human,
                           code gate)             code gate) code gate)  interrupt)
```

- **Discover** segments the transcript into numbered, speaker-attributed lines. No model.
- **Extract** asks the model for requirements, use cases, open items and contradictions with a quote per claim. Code then checks that every quote is a verbatim substring of the cited line. A quote found on another line is repaired and recorded; anything else is dropped and recorded. The speaker comes from the transcript, never from the model.
- **Retrieve** searches a small synthetic pattern library with SQLite full-text search.
- **Design** drafts a brief in the working shape of a solution architecture spec: snapshot, use cases with readiness, constraints, phases with exit criteria, success measures with baseline status, risks, open items with owner roles. Code strips citations to passages that were not retrieved and classifies every number as said by the customer, taken from reference material, or from nowhere.
- **Critique** has the model read the brief against the transcript, then merges code findings: dropped evidence, unverified numbers, invalid citations, unaddressed contradictions.
- **Gate** is a LangGraph interrupt. The engineer approves, requests changes with a note (back to design), or answers open items (back to extract, with the answers as new attributed lines). A vague answer such as "we don't know yet" cannot close an item, whatever the model says.

## Demo path (three minutes)

```powershell
cd apps/api
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\uvicorn signalroom.main:app --port 8000
```

```powershell
cd apps/web
npm install
npm run dev
```

Open `http://localhost:5173`. Four synthetic rooms open from recorded model runs, no key needed. Pick a claim to see its verified quote and line. Read the critic findings; the ones tagged "code check" came from the gates, not the model. Type "we don't know yet" into an open item and re-run: it stays open. Approve, and the trace shows the graph reaching its end.

To analyse a new transcript you need a key. Copy `.env.example` to `apps/api/.env` and set one for any OpenAI-compatible endpoint (Groq by default, OpenRouter tested). The composer can load any of the ten synthetic fixtures.

## Evaluation results

Ten synthetic discovery calls, each with gold requirements, gold open items and planted traps, run through `openai/gpt-oss-120b` via OpenRouter and replayed from committed recordings. Full method, per-fixture rows and the failure list are in [docs/evaluation.md](docs/evaluation.md).

| Measure | Run 1 |
|---|---|
| Requirement recall / precision (mean) | 0.95 / 0.87 |
| Open item recall (mean) | 0.75 |
| Model quotes passing the verbatim check | 119 of 119 |
| Injection lines ignored | 4 of 4 |
| Planted numbers kept out of the brief | 2 of 2 |
| Gaps kept open | 15 of 17 |
| Contradictions surfaced | 3 of 8 |
| Vague follow-up answers kept open / definite answers closed | 6 of 6 / 5 of 6 |
| Rooms the critic sent back | 10 of 10 |
| Latency per room, three model calls | about 31 s mean, 108 s max |
| Cost per room at listed prices | under $0.002 |

What failed, honestly: the model rarely records a contradiction when one speaker corrects another (eight cameras, then five working), and it pads "TBC" durations with estimates, which the number check flags in every room. Both are prompt problems. A second run with revised prompts was started and stopped by a provider credit limit; the changes are queued, not claimed.

The grounding gate fired zero times on real runs. It is kept anyway: a guarantee that costs nothing when the model behaves is still a guarantee, and the unit tests prove it fires when the model does not.

## Architecture and decisions

- [docs/architecture.md](docs/architecture.md): the shape, the trust model, what was left out on purpose.
- [docs/DECISIONS.md](docs/DECISIONS.md): each non-obvious choice with its alternative and cost, including why FTS5 beat a vector database here, why the graph kept LangGraph, and what run 1 changed.
- [AUDIT.md](AUDIT.md): the audit of the original build that this work started from.

Stack: FastAPI, LangGraph with a SQLite checkpointer, Pydantic strict-schema structured output over an OpenAI-compatible client, SQLite FTS5, React and Vite. Model calls are recorded by content hash and replayed in CI (`apps/api/recordings/`).

## Limitations

- Synchronous runs: a live room takes twenty seconds to two minutes depending on the provider route, with no streaming.
- The contradiction detector is the model; code only checks that cited lines exist.
- Ten fixtures is enough to show the failure modes, not to estimate rates with confidence.
- No authentication, no multi-tenant rooms, no hosted deployment. Local demo state is rebuilt, not migrated.
- The read-only MCP server exposes search, rooms and evaluation results; approval is never exposed.

## Built with AI assistance

Built by Priyanshu Yogi with Codex (initial scaffold), Claude (audit, rebuild, evaluation, documentation) and the Impeccable design skill. The commit history is the real order of work. Every product decision, the synthetic-data rule and the final calls were his.
