# Decisions

Each entry is a choice that could reasonably have gone another way, what was chosen, and why. Dates are when the decision was made.

## 2026-09-06 · Reposition away from "voice-first"

**Choice.** Drop voice capture and transcription entirely. The product takes a text transcript.

**Why.** Voice was a thin adapter behind a paid key that nobody could run without credentials, and call transcripts arrive as text from the meeting tool anyway. Leading with it made the pitch about a feature that proved nothing. The proof is in what happens to the transcript afterwards.

**Alternative.** Keep voice as an optional input. Rejected because every optional path is one more thing to defend in an interview and one more thing that can look broken in a demo.

## 2026-09-06 · Make the LangGraph real, with the gate as an interrupt

**Choice.** Every node does its own work. The approval gate is a LangGraph `interrupt`; the API resumes the same thread with the human decision, and the decision can send the graph back to design (request changes) or to extract (follow-up answers).

**Why.** The original graph had four pass-through nodes handed a finished answer, which is worse than no graph. A plain pipeline would have been honest too, but the workflow genuinely has a pause point with three exits, and checkpointed resumption after a restart is a real property of the product, not decoration. The trace endpoint now shows real checkpoints.

**Cost.** One more dependency and a SQLite checkpoint file. State is stored as plain dicts so the checkpointer never sees domain classes.

**Alternative.** A plain Python pipeline with a stage log. It would be about a hundred lines shorter and equally explainable. Chosen against because the interrupt is the one place LangGraph earns its keep here.

## 2026-09-06 · SQLite full-text search instead of a vector database

**Choice.** Retrieval is BM25 through SQLite FTS5 with Porter stemming, a title boost, and a floor of two shared content terms.

**Why.** The pattern library is a few dozen passages. The previous "vector search" hashed tokens into 192 dimensions, so `alert` and `alerts` had a cosine similarity of zero, and every query returned four hits whatever their relevance. FTS5 is in the standard library, deterministic, and honest about what it is.

**Swap point.** `KnowledgeStore.add / search / count`. If the corpus grows past a few thousand passages, embeddings plus a reranker go behind the same interface.

## 2026-09-06 · Code decides what the model may claim

**Choice.** Three code gates, none of which the model can talk its way past:

1. Every requirement and use case must quote a verbatim substring of the line it cites. A quote found on a different line is repaired and recorded. Anything else is dropped and recorded. The speaker comes from the transcript, never from the model.
2. Every number in the brief is classified: said by the customer (after folding number words such as "thirty" to digits), present only in reference material (flagged medium), or present nowhere (flagged high). Citations to passages that were not retrieved are stripped. A "proven pattern" with no citation is downgraded to unknown.
3. A follow-up answer that says the customer does not know, will check, or is unsure cannot close an open item, even when the model marks it resolved.

**Why.** Prompt instructions are requests. A hiring lead's first question is "what happens when the model ignores them", and the answer has to be "this code".

**What it cost in the first live run.** The number check raised 23 high findings on the first room, most of them false positives from number words and Unicode hyphens. Fixed the same day; the genuinely invented numbers were still caught. Recorded in `docs/evaluation.md`.

## 2026-09-06 · Record and replay model calls by content hash

**Choice.** Every model call is keyed by a hash of model, prompts and schema. Recordings hold the full request and parsed response. Modes: `auto` (replay when a recording exists, else live), `live`, `replay` (never network), `record` (fill missing recordings).

**Why.** The demo has to work with no key, CI has to be free and reproducible, and a reader should be able to see exactly which prompt produced which output. A prompt change moves the hash, so stale recordings cannot be replayed by accident; only the changed stage is re-recorded.

**Tradeoff.** Recordings are committed to the repo (a few hundred kilobytes). Latency numbers in replay are the recorded ones, labelled as such.

## 2026-09-06 · Provider routing through OpenRouter

**Choice.** The client speaks the OpenAI chat API with a configurable base URL. The key on hand was an OpenRouter key, so the default routes there with `provider.require_parameters` set, and `max_tokens` rather than `max_completion_tokens`.

**Why.** OpenRouter fans one model id out to many providers, not all of which enforce a JSON schema. Requiring the parameters makes routing fail loudly instead of returning unconstrained text. The first attempt failed exactly this way until the token parameter name was changed.

**Observed.** `openai/gpt-oss-120b` spends thousands of reasoning tokens per stage; a three-stage room takes roughly one to two minutes and costs under a cent at OpenRouter's listed prices. Latency variance between providers is large (11 s to 240 s for the same stage). Both are reported per run rather than hidden.

## 2026-09-06 · Synthetic fixtures with planted traps

**Choice.** Ten invented discovery calls, five speakers each, with gold requirements and open items as term rubrics, and traps: injection lines, numbers seeded in the reference library, speaker contradictions, deliberate gaps, and follow-up scenarios.

**Why.** An evaluation that cannot fail is a regression test wearing an evaluation's clothes. Traps make the failure modes that matter for this product observable. Rubric matching tolerates paraphrase; unmatched extractions still count against precision and are listed so they can be reviewed by hand rather than relabelled to inflate the score.

**Rule.** Nothing in any fixture derives from a real engagement. The vault this project drew vocabulary from stays closed.

## 2026-09-06 · What run 1 changed

**Observed.** Ten fixtures, 119 model quotes, every one a verbatim substring of its cited line: the grounding gate never had to repair or drop anything on a real run. Injection lines were ignored 4 of 4 times, planted numbers stayed out of the brief 2 of 2 times. The misses were elsewhere: the model recorded only 3 of 8 planted contradictions, treating a correction ("eight cameras" then "five working") as resolved rather than disputed, and it wrote numbers nobody stated, mostly exit-criteria targets, which the number check flagged in six of ten rooms. One room padded durations as "TBC (expected 1 to 2 weeks)"; the check passed those because 1 and 2 appear elsewhere in that transcript.

*Corrected 2026-10-09.* This entry first said the padded durations were flagged in every room. A replay of the run 1 recordings showed the current check does not flag them, and that six of the sixteen number findings it did raise came from passage citation ids such as `operational-alert-design#5` being read as numbers. The check now strips citation ids before it looks for numbers.

**Choice.** Keep the gate exactly as it is even though it fired zero times on real runs. A guarantee that costs nothing when the model behaves is still a guarantee. Change the two prompts, not the checks: contradictions should explicitly include corrections and reversals, and durations must be exactly "TBC". Re-record everything as run 2 and report both runs side by side.

**Status.** Run 2 was started and stopped by the provider: OpenRouter returned 402 (credit budget exhausted) on nine of ten fixtures. The prompt changes are reverted in the tree so the committed recordings still replay, and they are queued for the next funded run. The first fixture that did complete under the new prompts still missed its same-speaker contradiction, so the contradiction fix is unproven; treat it as a hypothesis.

**Not done.** Relabelling gold items that the model expressed differently. Unmatched extractions are listed per fixture and reviewed by hand; the scores stay as the rubric produced them.

## 2026-10-27 · What the contradiction detector changed

**Observed.** Four of run 1's five missed contradictions had the same shape: a speaker corrects the previous speaker's figure on the very next line (eight cameras, then five of the eight working; four packing lines, then three; fifteen, then the signs say twenty-five; twelve hundred tickets, then four hundred). The fifth is different in kind: the gateway "is staying" at L7 against a proposal to replace it at L26, nineteen lines apart, with no figures.

**Choice.** Catch the figure corrections in code instead of waiting on a prompt. `numeric_corrections()` flags two consecutive lines by different speakers when the reply opens with a different figure, or restates the earlier figure beside a new one. On the ten transcripts alone it finds those four pairs and fires nowhere else. It runs after the critique call, so the recorded prompts are unchanged and run 1's model outputs replay exactly. That isolates what the code moved from anything the model did.

| Measure | Run 1 | Run 1 outputs + detector |
|---|---|---|
| Run | 20260908T171415Z, replay | 20261027T075316Z, replay |
| Requirement recall / precision | 0.948 / 0.865 | 0.948 / 0.865 |
| Open item recall | 0.75 | 0.75 |
| Quotes verified verbatim | 119 of 119 | 119 of 119 |
| Injection, planted number, gap | 4 of 4, 2 of 2, 15 of 17 | 4 of 4, 2 of 2, 15 of 17 |
| Contradiction | 3 of 8 | 7 of 8 |
| Critique findings (high) | 48 (31) | 52 (31) |

The four new findings are medium-severity code checks, so no room's verdict changed. Merged with the citation-id fix to the number check, the replay on main (20261027T075823Z) keeps every number above and has 46 findings, 25 high: six false "unverified number" findings are gone.

**Status.** The prompt half of the run 1 plan is still a hypothesis. Run 2 under the revised prompts could not be recorded: the OpenRouter account has never been funded (balance below zero after free usage), so a paid model call returns 402. The two prompt edits are committed on branch `run-2-prompts`, unrecorded; replay fails on that branch until a funded record run fills in its recordings.

**Not done.** A detector for the Northstar kind of contradiction, a fact and a later reversal far apart; that needs meaning, not figures, and stays with the model. Corrections separated by an interjection are not caught; the check looks at consecutive lines only. The detector runs after the brief is drafted, so the brief does not yet address what it finds; move it into extraction at the next record run.

## 2026-09-06 · Local schema is versioned and rebuilt, not migrated

**Choice.** `PRAGMA user_version` on the rooms database. A mismatch drops and recreates the tables.

**Why.** The API failed to start on a database left over from the original code because `CREATE TABLE IF NOT EXISTS` kept the old columns. This is local demo state re-seeded from recordings, so a migration framework would be ceremony.

## 2026-09-06 · MCP stays read-only

**Choice.** The MCP server exposes search, room reads and evaluation results. Nothing that creates, changes or approves a room.

**Why.** The gate is the product's promise. Exposing it through a tool interface would make "human approval" a claim rather than a property.
