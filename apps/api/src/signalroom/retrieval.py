import hashlib
import math
import os
import re
import atexit
from pathlib import Path
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from .models import KnowledgeDocument, SearchHit

DIMENSIONS = 192
COLLECTION = "solutioning_knowledge"


def embed(text: str) -> list[float]:
    """Dependency-free hashing embeddings for a reproducible local demo."""
    vector = [0.0] * DIMENSIONS
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    for token in tokens:
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "little") % DIMENSIONS
        sign = 1 if digest[4] % 2 else -1
        vector[index] += sign * (1 + min(len(token), 12) / 12)
    norm = math.sqrt(sum(value * value for value in vector)) or 1
    return [value / norm for value in vector]


class KnowledgeStore:
    def __init__(self) -> None:
        data_dir = Path(os.getenv("SIGNALROOM_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.client = QdrantClient(path=str(data_dir / "qdrant"))
        if not self.client.collection_exists(COLLECTION):
            self.client.create_collection(COLLECTION, vectors_config=VectorParams(size=DIMENSIONS, distance=Distance.COSINE))

    def add(self, document: KnowledgeDocument) -> int:
        passages = [part.strip() for part in re.split(r"\n\s*\n|(?<=[.!?])\s+(?=[A-Z])", document.content) if len(part.strip()) > 25]
        points = [PointStruct(id=str(uuid4()), vector=embed(passage), payload={"title": document.title, "passage": passage, "source": document.source}) for passage in passages]
        if points:
            self.client.upsert(COLLECTION, points)
        return len(points)

    def search(self, query: str, limit: int = 4) -> list[SearchHit]:
        response = self.client.query_points(collection_name=COLLECTION, query=embed(query), limit=limit, with_payload=True)
        return [SearchHit(title=str(hit.payload.get("title")), passage=str(hit.payload.get("passage")), source=str(hit.payload.get("source")), score=round(float(hit.score), 3)) for hit in response.points]


store = KnowledgeStore()
atexit.register(store.client.close)
if store.client.count(COLLECTION).count == 0:
    for seed in [
        KnowledgeDocument(title="Telemetry integration pattern", source="synthetic pattern library", content="Prefer read-only ingestion during a proof of concept. Confirm authentication, rate limits, timestamp semantics, data retention, and backfill behavior before committing the integration design."),
        KnowledgeDocument(title="Operational alert design", source="synthetic pattern library", content="Alert thresholds should be calibrated against historical events. Every notification should retain the triggering evidence, threshold version, acknowledgement state, and responsible reviewer."),
        KnowledgeDocument(title="PoC measurement guide", source="synthetic pattern library", content="A proof of concept requires a baseline, a named metric owner, a measurement window, and an explicit acceptance threshold. Avoid invented improvement percentages when no baseline exists."),
    ]:
        store.add(seed)
