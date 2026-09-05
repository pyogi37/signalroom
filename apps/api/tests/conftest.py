import os
import tempfile
from pathlib import Path

# Point every SQLite file at a throwaway directory before the package is imported,
# so tests never touch apps/api/data or apps/api/recordings.
_TEMP = Path(tempfile.mkdtemp(prefix="signalroom-tests-"))
os.environ.setdefault("SIGNALROOM_DATA_DIR", str(_TEMP / "data"))
os.environ.setdefault("SIGNALROOM_RECORDINGS_DIR", str(_TEMP / "recordings"))
os.environ.setdefault("SIGNALROOM_MODEL_MODE", "replay")
os.environ.setdefault("SIGNALROOM_SKIP_SEED", "1")
for key in ("GROQ_API_KEY", "OPENAI_API_KEY", "SIGNALROOM_MODEL_API_KEY"):
    os.environ.pop(key, None)
