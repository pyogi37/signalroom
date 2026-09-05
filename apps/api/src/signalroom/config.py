"""Process-wide settings read from the environment.

Everything here has a safe default so the API, the tests and the evaluation
suite run without any configuration. Secrets are only ever read from the
environment; nothing in this module writes them anywhere.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# apps/api/.env holds the model key on a developer machine. It is gitignored.
# Real environment variables take precedence over the file.
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


def data_dir() -> Path:
    """Directory for SQLite files and other local state. Created on first use."""
    default = Path(__file__).resolve().parents[2] / "data"
    path = Path(os.getenv("SIGNALROOM_DATA_DIR", default))
    path.mkdir(parents=True, exist_ok=True)
    return path


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()
