import json

import pytest
from pydantic import BaseModel

from signalroom import model_client
from signalroom.model_client import ModelUnavailable, recording_key, structured_call


class Answer(BaseModel):
    value: str
    count: int


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("SIGNALROOM_RECORDINGS_DIR", str(tmp_path))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SIGNALROOM_MODEL_API_KEY", raising=False)
    monkeypatch.delenv("SIGNALROOM_PRICE_INPUT_PER_M", raising=False)
    monkeypatch.delenv("SIGNALROOM_PRICE_OUTPUT_PER_M", raising=False)
    return tmp_path


def write_recording(directory, key, response, input_tokens=120, output_tokens=40):
    (directory / f"{key}.json").write_text(json.dumps({
        "key": key, "stage": "test", "model": "recorded-model", "latency_ms": 321.5,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        "request": {"system": "s", "user": "u", "schema": "Answer"},
        "response": response,
    }), encoding="utf-8")


def test_key_depends_on_every_input():
    base = recording_key("m", "sys", "user", "Answer")
    assert base != recording_key("m2", "sys", "user", "Answer")
    assert base != recording_key("m", "sys2", "user", "Answer")
    assert base != recording_key("m", "sys", "user2", "Answer")
    assert base != recording_key("m", "sys", "user", "Other")
    assert base == recording_key("m", "sys", "user", "Answer")


def test_replay_without_recording_is_a_clear_error(isolated, monkeypatch):
    monkeypatch.setenv("SIGNALROOM_MODEL_MODE", "replay")
    with pytest.raises(ModelUnavailable) as failure:
        structured_call("extract", "sys", "user", Answer)
    assert "GROQ_API_KEY" in str(failure.value)


def test_auto_without_key_or_recording_is_a_clear_error(isolated, monkeypatch):
    monkeypatch.setenv("SIGNALROOM_MODEL_MODE", "auto")
    assert model_client.live_model_enabled() is False
    with pytest.raises(ModelUnavailable):
        structured_call("extract", "sys", "user", Answer)


def test_auto_serves_a_recording_and_reports_replay(isolated, monkeypatch):
    monkeypatch.setenv("SIGNALROOM_MODEL_MODE", "auto")
    monkeypatch.setenv("SIGNALROOM_MODEL", "some-model")
    key = recording_key("some-model", "sys", "user", "Answer")
    write_recording(isolated, key, {"value": "ok", "count": 2})
    parsed, call = structured_call("extract", "sys", "user", Answer)
    assert parsed == Answer(value="ok", count=2)
    assert call.mode == "replay"
    assert call.model == "recorded-model"
    assert call.latency_ms == 321.5
    assert (call.input_tokens, call.output_tokens) == (120, 40)
    assert call.estimated_cost_usd is None
    assert call.recording_key == key


def test_cost_estimate_uses_configured_prices(isolated, monkeypatch):
    monkeypatch.setenv("SIGNALROOM_MODEL_MODE", "replay")
    monkeypatch.setenv("SIGNALROOM_MODEL", "some-model")
    monkeypatch.setenv("SIGNALROOM_PRICE_INPUT_PER_M", "0.15")
    monkeypatch.setenv("SIGNALROOM_PRICE_OUTPUT_PER_M", "0.60")
    key = recording_key("some-model", "sys", "user", "Answer")
    write_recording(isolated, key, {"value": "ok", "count": 1}, input_tokens=1_000_000, output_tokens=500_000)
    _, call = structured_call("extract", "sys", "user", Answer)
    assert call.estimated_cost_usd == pytest.approx(0.15 + 0.30)


def test_recording_that_no_longer_matches_the_schema_fails_loudly(isolated, monkeypatch):
    monkeypatch.setenv("SIGNALROOM_MODEL_MODE", "replay")
    monkeypatch.setenv("SIGNALROOM_MODEL", "some-model")
    key = recording_key("some-model", "sys", "user", "Answer")
    write_recording(isolated, key, {"value": "ok"})
    with pytest.raises(Exception):
        structured_call("extract", "sys", "user", Answer)


def test_describe_reports_mode_and_provider(isolated, monkeypatch):
    monkeypatch.setenv("SIGNALROOM_MODEL_MODE", "auto")
    monkeypatch.setenv("SIGNALROOM_MODEL_BASE_URL", "https://example.test/v1")
    info = model_client.describe()
    assert info["mode"] == "auto"
    assert info["live"] is False
    assert info["provider_host"] == "example.test"
    assert info["recordings"] == 0
