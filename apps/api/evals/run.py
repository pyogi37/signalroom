import json
from pathlib import Path

from signalroom.analysis import analyze
from signalroom.evaluation import evaluate
from signalroom.models import AnalyzeRequest


fixtures = json.loads((Path(__file__).parent / "fixtures.json").read_text(encoding="utf-8"))
results = []

for fixture in fixtures:
    session = analyze(AnalyzeRequest(organization=fixture["organization"], transcript=fixture["transcript"]))
    actual = {item.title for item in session.requirements}
    expected = set(fixture["expected_titles"])
    results.append({
        "fixture": fixture["name"],
        "recall": len(actual & expected) / len(expected),
        "precision": len(actual & expected) / len(actual),
        "grounding": evaluate(session)["grounding_rate"],
        "unexpected": sorted(actual - expected),
        "missing": sorted(expected - actual),
    })

summary = {
    "fixtures": len(results),
    "mean_recall": round(sum(item["recall"] for item in results) / len(results), 3),
    "mean_precision": round(sum(item["precision"] for item in results) / len(results), 3),
    "mean_grounding": round(sum(item["grounding"] for item in results) / len(results), 3),
    "results": results,
}
print(json.dumps(summary, indent=2))

if summary["mean_recall"] < 1 or summary["mean_grounding"] < 1:
    raise SystemExit(1)
