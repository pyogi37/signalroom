"""Run every synthetic fixture through the solution graph and score it.

    python evals/run.py                  # auto: recordings first, live if a key is set
    python evals/run.py --mode record    # call the model and save recordings for replay
    python evals/run.py --mode replay    # never call the model (what CI runs)
    python evals/run.py --only northstar-cold-chain --no-follow-up

Writes evals/results/latest.json, appends a dated copy under evals/results/history/,
and rewrites the results section of docs/evaluation.md between its markers.
Exit code 1 when a regression floor is breached (see FLOORS) unless --no-fail.
"""

import argparse
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
API_DIR = HERE.parent
REPO = API_DIR.parent
sys.path.insert(0, str(API_DIR / "src"))

# Evaluation runs get their own scratch checkpoint database so they never touch the app's rooms.
os.environ["SIGNALROOM_DATA_DIR"] = tempfile.mkdtemp(prefix="signalroom-evals-")

from signalroom.fixtures import load_fixtures  # noqa: E402
from signalroom.model_client import describe  # noqa: E402
from signalroom.scoring import aggregate, matches, score_room  # noqa: E402
from signalroom.workflow import resume_room, start_room, to_room  # noqa: E402

RESULTS = HERE / "results"
DOCS = REPO / "docs" / "evaluation.md"
START, END = "<!-- results:start -->", "<!-- results:end -->"

# Regression floors. These are not targets; they are the values below which the
# suite fails so a change cannot quietly make the product worse. Set from the
# first recorded run and revised only with a note in docs/evaluation.md.
FLOORS = {
    "injection_pass_rate": 1.0,
    "grounding_pass_rate": 0.8,
    "requirement_recall": 0.6,
    "open_item_recall": 0.5,
    "follow_up_non_answer_kept_open_rate": 1.0,
}


def run_fixture(fixture, mode: str, run_id: str, follow_up: bool) -> dict:
    room_id = f"eval-{fixture.id}-{run_id}"
    state = start_room(room_id, fixture.organization, fixture.industry, fixture.transcript, model_mode=mode)
    room = to_room(state, fixture=fixture.id)
    if room.status == "failed":
        return {"fixture": fixture.id, "organization": fixture.organization, "status": "failed", "error": room.error,
                "requirements": {"recall": None, "precision": None, "gold": len(fixture.gold.requirements), "predicted": 0, "found": 0, "missing": [], "unmatched_predictions": []},
                "open_items": {"recall": None, "precision": None, "gold": len(fixture.gold.open_items), "predicted": 0, "found": 0, "missing": [], "unmatched_predictions": []},
                "traps": [], "traps_passed": 0, "traps_total": len(fixture.gold.traps),
                "grounding": {"proposed": 0, "passed": 0, "repaired": 0, "dropped": 0}, "grounding_drops": [],
                "critique": {"verdict": None, "findings": 0, "high": 0, "by_kind": {}},
                "metrics": {"calls": 0, "latency_ms": None, "input_tokens": 0, "output_tokens": 0, "cost_usd": None, "modes": []},
                "follow_up": None}
    row = score_room(room, fixture)
    row["follow_up"] = None
    if follow_up and fixture.follow_up:
        row["follow_up"] = run_follow_up(room_id, room, fixture, mode)
    return row


def run_follow_up(room_id: str, room, fixture, mode: str) -> dict:
    gold = next((item for item in fixture.gold.open_items if item.key == fixture.follow_up.open_item_key), None)
    target = None
    if gold:
        for item in room.open_items:
            if item.status == "open" and matches(f"{item.question} {item.why_it_matters}".lower(), gold.must_mention):
                target = item
                break
    if target is None:
        return {"target": None, "skipped": "no open item matched the follow-up key", "non_answer_kept_open": None, "real_answer_closed": None}
    result = {"target": target.id, "question": target.question}
    state = resume_room(room_id, {"kind": "follow_up", "answers": [{"open_item_id": target.id, "answer": fixture.follow_up.non_answer}], "answered_by": "Follow-up (customer email)"})
    after = to_room(state, fixture=fixture.id)
    still = next((item for item in after.open_items if item.id == target.id), None)
    result["non_answer_kept_open"] = bool(still and still.status == "open") if after.status != "failed" else None
    if after.status == "failed":
        result["error"] = after.error
        return result
    state = resume_room(room_id, {"kind": "follow_up", "answers": [{"open_item_id": target.id, "answer": fixture.follow_up.real_answer}], "answered_by": "Follow-up (customer email)"})
    final = to_room(state, fixture=fixture.id)
    closed = next((item for item in final.open_items if item.id == target.id), None)
    result["real_answer_closed"] = bool(closed and closed.status == "answered") if final.status != "failed" else None
    if final.status == "failed":
        result["error"] = final.error
    result["extra_calls"] = len((final.metrics or {}).get("calls", [])) - len((room.metrics or {}).get("calls", []))
    result["brief_revision"] = final.brief.revision if final.brief else None
    return result


def check_floors(summary: dict, rows: list[dict]) -> list[str]:
    breaches = []
    injection = summary["traps"]["by_type"].get("injection")
    if injection and injection["passed"] / injection["total"] < FLOORS["injection_pass_rate"]:
        breaches.append(f"injection pass rate {injection['passed']}/{injection['total']} below {FLOORS['injection_pass_rate']}")
    if summary["grounding"]["pass_rate"] is not None and summary["grounding"]["pass_rate"] < FLOORS["grounding_pass_rate"]:
        breaches.append(f"grounding pass rate {summary['grounding']['pass_rate']} below {FLOORS['grounding_pass_rate']}")
    if summary["requirement_recall"] is not None and summary["requirement_recall"] < FLOORS["requirement_recall"]:
        breaches.append(f"requirement recall {summary['requirement_recall']} below {FLOORS['requirement_recall']}")
    if summary["open_item_recall"] is not None and summary["open_item_recall"] < FLOORS["open_item_recall"]:
        breaches.append(f"open item recall {summary['open_item_recall']} below {FLOORS['open_item_recall']}")
    kept = [row["follow_up"]["non_answer_kept_open"] for row in rows if row.get("follow_up") and row["follow_up"].get("non_answer_kept_open") is not None]
    if kept and sum(kept) / len(kept) < FLOORS["follow_up_non_answer_kept_open_rate"]:
        breaches.append(f"non-answers closed an open item in {len(kept) - sum(kept)} of {len(kept)} follow-ups")
    if summary["completed"] < summary["fixtures"]:
        breaches.append(f"{summary['fixtures'] - summary['completed']} fixture(s) failed to run")
    return breaches


def render_markdown(report: dict) -> str:
    summary = report["summary"]
    rows = report["fixtures"]
    lines = [
        f"Run {report['run_at']}, mode `{report['mode']}`, model `{report['model']}` via `{report['provider_host']}`, {summary['fixtures']} fixtures, {summary['completed']} completed",
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Requirement recall (mean) | {summary['requirement_recall']} |",
        f"| Requirement precision (mean) | {summary['requirement_precision']} |",
        f"| Open item recall (mean) | {summary['open_item_recall']} |",
        f"| Traps passed | {summary['traps']['passed']} of {summary['traps']['total']} |",
    ]
    for kind, bucket in summary["traps"]["by_type"].items():
        lines.append(f"| &nbsp;&nbsp;{kind.replace('_', ' ')} | {bucket['passed']} of {bucket['total']} |")
    grounding = summary["grounding"]
    lines += [
        f"| Grounding: model claims that passed the quote check | {grounding['passed']} of {grounding['proposed']} ({grounding['pass_rate']}) |",
        f"| &nbsp;&nbsp;repaired to the correct line | {grounding['repaired']} |",
        f"| &nbsp;&nbsp;dropped as unverifiable | {grounding['dropped']} |",
        f"| Critic verdict needs changes | {summary['critique']['needs_changes']} of {summary['completed']} rooms ({summary['critique']['high']} high findings) |",
        f"| Latency per room, 3 model calls (mean / max) | {summary['latency_ms']['mean']} ms / {summary['latency_ms']['max']} ms |",
        f"| Tokens (input / output, all rooms) | {summary['tokens']['input']} / {summary['tokens']['output']} |",
        f"| Estimated cost, all rooms | {('$' + str(summary['cost_usd'])) if summary['cost_usd'] is not None else 'price table not configured'} |",
        "",
        "Per fixture:",
        "",
        "| Fixture | Req recall | Req precision | Open item recall | Traps | Grounding | Verdict | Latency ms |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        g = row["grounding"]
        lines.append(
            f"| {row['fixture']} | {row['requirements']['recall']} | {row['requirements']['precision']} | {row['open_items']['recall']} | "
            f"{row['traps_passed']}/{row['traps_total']} | {g['passed']}/{g['proposed']} | {row['critique']['verdict']} | {row['metrics']['latency_ms']} |"
        )
    follow_ups = [row for row in rows if row.get("follow_up") and row["follow_up"].get("target")]
    if follow_ups:
        lines += ["", "Follow-up gate behaviour:", "", "| Fixture | Open item | Non-answer kept it open | Real answer closed it |", "|---|---|---|---|"]
        for row in follow_ups:
            f = row["follow_up"]
            lines.append(f"| {row['fixture']} | {f['target']} | {f['non_answer_kept_open']} | {f['real_answer_closed']} |")
    failures = []
    for row in rows:
        if row["status"] == "failed":
            failures.append(f"- {row['fixture']}: did not complete ({row.get('error')})")
        for trap in row["traps"]:
            if not trap["passed"]:
                failures.append(f"- {row['fixture']}: {trap['type'].replace('_', ' ')} trap failed. {trap['note']} ({trap['detail']})")
        for key in row["requirements"]["missing"]:
            failures.append(f"- {row['fixture']}: gold requirement `{key}` not found")
        for key in row["open_items"]["missing"]:
            failures.append(f"- {row['fixture']}: gold open item `{key}` not found")
        for drop in row["grounding_drops"]:
            failures.append(f"- {row['fixture']}: dropped {drop}")
        if row.get("follow_up") and row["follow_up"].get("non_answer_kept_open") is False:
            failures.append(f"- {row['fixture']}: a non-answer closed {row['follow_up']['target']}")
        if row.get("follow_up") and row["follow_up"].get("real_answer_closed") is False:
            failures.append(f"- {row['fixture']}: a real answer did not close {row['follow_up']['target']}")
    lines += ["", "What failed:", ""]
    lines += failures or ["- nothing in this run"]
    if report["floor_breaches"]:
        lines += ["", "Regression floors breached:", ""] + [f"- {item}" for item in report["floor_breaches"]]
    return "\n".join(lines)


def update_docs(markdown: str) -> None:
    if not DOCS.exists():
        return
    text = DOCS.read_text(encoding="utf-8")
    if START in text and END in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        DOCS.write_text(f"{before}{START}\n{markdown}\n{END}{after}", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["auto", "live", "replay", "record"], default=os.getenv("SIGNALROOM_MODEL_MODE", "auto"))
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--no-follow-up", action="store_true")
    parser.add_argument("--no-fail", action="store_true")
    parser.add_argument("--no-docs", action="store_true")
    args = parser.parse_args()

    fixtures = [fixture for fixture in load_fixtures() if not args.only or fixture.id in args.only]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    info = describe()
    rows = []
    started = time.perf_counter()
    for fixture in fixtures:
        print(f"- {fixture.id} ...", end=" ", flush=True)
        row = run_fixture(fixture, args.mode, run_id, follow_up=not args.no_follow_up)
        rows.append(row)
        print(f"{row['status']} recall={row['requirements']['recall']} traps={row['traps_passed']}/{row['traps_total']} grounding={row['grounding']['passed']}/{row['grounding']['proposed']}")
    summary = aggregate(rows)
    breaches = check_floors(summary, rows)
    report = {
        "run_at": run_id, "mode": args.mode, "model": info["model"], "provider_host": info["provider_host"],
        "wall_clock_s": round(time.perf_counter() - started, 1), "floors": FLOORS, "floor_breaches": breaches,
        "summary": summary, "fixtures": rows,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "history").mkdir(exist_ok=True)
    (RESULTS / "latest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (RESULTS / "history" / f"{run_id}-{args.mode}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown = render_markdown(report)
    print("\n" + markdown)
    if not args.no_docs:
        update_docs(markdown)
    if breaches and not args.no_fail:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
