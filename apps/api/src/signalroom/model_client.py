"""Structured-output model client with recording and replay.

One function, `structured_call`, sends a system and user message to an
OpenAI-compatible chat endpoint (Groq by default) and returns a validated
Pydantic object plus a `ModelCall` record with latency, tokens and an
estimated cost.

Every call is addressed by a content hash of (model, system, user, schema).
That hash names a JSON file under `apps/api/recordings/`. The mode decides
what happens:

- `replay`: read the recording; never call the network. Raise
  `ModelUnavailable` if there is no recording.
- `live`: always call the network; never write a recording.
- `record`: call the network and write the recording.
- `auto` (default): use a recording when one exists, otherwise call live if a
  key is configured, otherwise raise `ModelUnavailable`.

Recordings hold the full request text and the parsed response, so anyone can
read exactly which prompt produced which output. All transcripts that reach
this client are synthetic.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import TypeVar

from pydantic import BaseModel

from .config import env

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"
RECORDINGS_DIR = Path(__file__).resolve().parents[2] / "recordings"

T = TypeVar("T", bound=BaseModel)


class ModelUnavailable(RuntimeError):
    """No key and no recording: the call cannot be served."""


class ModelCallFailed(RuntimeError):
    """The provider answered with an error, a refusal, or unparsable output."""


@dataclass
class ModelCall:
    stage: str
    model: str
    mode: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None
    recording_key: str

    def as_dict(self) -> dict:
        return asdict(self)


def api_key() -> str:
    return env("SIGNALROOM_MODEL_API_KEY") or env("GROQ_API_KEY") or env("OPENAI_API_KEY")


def base_url() -> str:
    return env("SIGNALROOM_MODEL_BASE_URL", DEFAULT_BASE_URL)


def model_name() -> str:
    return env("SIGNALROOM_MODEL", DEFAULT_MODEL)


def configured_mode() -> str:
    value = env("SIGNALROOM_MODEL_MODE", "auto").lower()
    return value if value in {"auto", "live", "replay", "record"} else "auto"


def recordings_dir() -> Path:
    path = Path(env("SIGNALROOM_RECORDINGS_DIR") or RECORDINGS_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def live_model_enabled() -> bool:
    return configured_mode() in {"live", "record"} or (configured_mode() == "auto" and bool(api_key()))


def describe() -> dict:
    return {
        "mode": configured_mode(),
        "live": live_model_enabled(),
        "model": model_name(),
        "provider_host": base_url().split("//")[-1].split("/")[0],
        "recordings": len(list(recordings_dir().glob("*.json"))),
    }


def recording_key(model: str, system: str, user: str, schema_name: str) -> str:
    payload = json.dumps({"model": model, "system": system, "user": user, "schema": schema_name}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def estimate_cost(input_tokens: int, output_tokens: int) -> float | None:
    """USD estimate from a configured price table; None when prices are not configured."""
    try:
        price_in = float(env("SIGNALROOM_PRICE_INPUT_PER_M"))
        price_out = float(env("SIGNALROOM_PRICE_OUTPUT_PER_M"))
    except ValueError:
        return None
    return round((input_tokens * price_in + output_tokens * price_out) / 1_000_000, 6)


def _replay(path: Path, schema: type[T], stage: str, key: str) -> tuple[T, ModelCall]:
    recorded = json.loads(path.read_text(encoding="utf-8"))
    parsed = schema.model_validate(recorded["response"])
    usage = recorded.get("usage", {})
    call = ModelCall(
        stage=stage, model=str(recorded.get("model", "")), mode="replay",
        latency_ms=float(recorded.get("latency_ms", 0.0)),
        input_tokens=int(usage.get("input_tokens", 0)), output_tokens=int(usage.get("output_tokens", 0)),
        estimated_cost_usd=estimate_cost(int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0))),
        recording_key=key,
    )
    return parsed, call


def _live(system: str, user: str, schema: type[T], stage: str, key: str, temperature: float, max_output_tokens: int) -> tuple[T, ModelCall, dict]:
    from openai import OpenAI

    if not api_key():
        raise ModelUnavailable(
            f"Stage '{stage}' needs a model. Set GROQ_API_KEY (or SIGNALROOM_MODEL_API_KEY) in apps/api/.env, "
            "or open a room that has recorded model output."
        )
    client = OpenAI(api_key=api_key(), base_url=base_url(), timeout=120.0, max_retries=2)
    extra_body: dict = {}
    if "openrouter.ai" in base_url():
        # Only route to providers that honour every parameter we send, including the JSON schema.
        extra_body["provider"] = {"require_parameters": True}
    started = perf_counter()
    try:
        completion = client.chat.completions.parse(
            model=model_name(),
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format=schema,
            temperature=temperature,
            max_tokens=max_output_tokens,
            extra_body=extra_body or None,
        )
    except Exception as error:  # provider errors are wrapped so the API can map them to one status
        raise ModelCallFailed(f"{type(error).__name__}: {error}") from error
    latency_ms = round((perf_counter() - started) * 1000, 1)
    message = completion.choices[0].message
    if getattr(message, "refusal", None):
        raise ModelCallFailed(f"Model refused the request: {message.refusal}")
    parsed = message.parsed
    if parsed is None:
        raise ModelCallFailed("Model returned no parsable structured output")
    usage = completion.usage
    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    call = ModelCall(
        stage=stage, model=completion.model or model_name(), mode="live", latency_ms=latency_ms,
        input_tokens=input_tokens, output_tokens=output_tokens,
        estimated_cost_usd=estimate_cost(input_tokens, output_tokens), recording_key=key,
    )
    recording = {
        "key": key,
        "stage": stage,
        "model": call.model,
        "provider_host": base_url().split("//")[-1].split("/")[0],
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "latency_ms": latency_ms,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        "request": {"system": system, "user": user, "schema": schema.__name__, "temperature": temperature},
        "response": parsed.model_dump(mode="json"),
    }
    return parsed, call, recording


def structured_call(
    stage: str,
    system: str,
    user: str,
    schema: type[T],
    *,
    temperature: float = 0.0,
    max_output_tokens: int = 8192,
    mode: str | None = None,
) -> tuple[T, ModelCall]:
    mode = mode if mode in {"auto", "live", "replay", "record"} else configured_mode()
    key = recording_key(model_name(), system, user, schema.__name__)
    path = recordings_dir() / f"{key}.json"

    if mode == "replay" or (mode == "auto" and path.exists()):
        if not path.exists():
            raise ModelUnavailable(
                f"Stage '{stage}' has no recorded model output and the client is in replay mode. "
                "Set GROQ_API_KEY in apps/api/.env to analyse new transcripts."
            )
        return _replay(path, schema, stage, key)

    parsed, call, recording = _live(system, user, schema, stage, key, temperature, max_output_tokens)
    if mode == "record":
        path.write_text(json.dumps(recording, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return parsed, call
