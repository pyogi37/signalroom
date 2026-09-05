"""Reference knowledge retrieval over SQLite full-text search.

The pattern library is a few dozen passages. That size does not justify a
vector database, so retrieval is BM25 through SQLite's FTS5 module with
Porter stemming. A passage is returned only when it ranks in the top results
and shares at least two content terms with the query, which keeps a single
common word from producing a "match". The swap point for embeddings, if the
corpus ever grows, is the `KnowledgeStore` interface: `add`, `search`, `count`.
"""

import re
import sqlite3
from pathlib import Path

from .config import data_dir
from .models import KnowledgeDocument, SearchHit

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "but", "by", "can", "do", "does", "for", "from",
    "has", "have", "how", "if", "in", "into", "is", "it", "its", "must", "no", "not", "of", "on", "or",
    "our", "should", "so", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this",
    "to", "us", "we", "what", "when", "which", "who", "will", "with", "would", "you", "your", "need", "needs",
    "want", "wants", "also", "just", "like", "any", "all", "each", "every", "more", "most", "some", "such",
}

MIN_SHARED_TERMS = 2


def _terms(text: str) -> list[str]:
    seen: list[str] = []
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        if len(token) >= 3 and token not in STOPWORDS and token not in seen:
            seen.append(token)
    return seen


def _stem(token: str) -> str:
    """A deliberately crude stem used only for the shared-term floor; FTS5 does the real stemming."""
    for suffix in ("ations", "ation", "ings", "ing", "ies", "ers", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def split_passages(content: str) -> list[str]:
    parts = re.split(r"\n\s*\n|(?<=[.!?])\s+(?=[A-Z])", content)
    return [part.strip() for part in parts if len(part.strip()) > 25]


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48]


class KnowledgeStore:
    def __init__(self, path: Path | str | None = None) -> None:
        location = str(path) if path else str(data_dir() / "knowledge.sqlite3")
        self.connection = sqlite3.connect(location, check_same_thread=False)
        self.connection.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS passages USING fts5("
            "title, passage, source UNINDEXED, passage_id UNINDEXED, tokenize='porter unicode61')"
        )
        self.connection.commit()

    def count(self) -> int:
        return int(self.connection.execute("SELECT count(*) FROM passages").fetchone()[0])

    def add(self, document: KnowledgeDocument) -> int:
        passages = split_passages(document.content)
        slug = _slug(document.title)
        existing = int(self.connection.execute(
            "SELECT count(*) FROM passages WHERE passage_id LIKE ?", (f"{slug}#%",)
        ).fetchone()[0])
        rows = [
            (document.title, passage, document.source, f"{slug}#{existing + index + 1}")
            for index, passage in enumerate(passages)
        ]
        if rows:
            self.connection.executemany(
                "INSERT INTO passages(title, passage, source, passage_id) VALUES (?, ?, ?, ?)", rows
            )
            self.connection.commit()
        return len(rows)

    def search(self, query: str, limit: int = 4) -> list[SearchHit]:
        terms = _terms(query)
        if not terms:
            return []
        match = " OR ".join(f'"{term}"' for term in terms[:40])
        rows = self.connection.execute(
            "SELECT title, passage, source, passage_id, bm25(passages, 3.0, 1.0) AS rank "
            "FROM passages WHERE passages MATCH ? ORDER BY rank LIMIT ?",
            (match, max(limit * 3, 12)),
        ).fetchall()
        query_stems = {_stem(term) for term in terms}
        hits: list[SearchHit] = []
        for title, passage, source, passage_id, rank in rows:
            passage_stems = {_stem(term) for term in _terms(f"{title} {passage}")}
            shared = len(query_stems & passage_stems)
            if shared < MIN_SHARED_TERMS:
                continue
            hits.append(SearchHit(
                passage_id=passage_id, title=title, passage=passage, source=source,
                score=round(-float(rank), 3), shared_terms=shared,
            ))
            if len(hits) >= limit:
                break
        return hits

    def get(self, passage_id: str) -> SearchHit | None:
        row = self.connection.execute(
            "SELECT title, passage, source, passage_id FROM passages WHERE passage_id = ?", (passage_id,)
        ).fetchone()
        if not row:
            return None
        return SearchHit(passage_id=row[3], title=row[0], passage=row[1], source=row[2], score=0.0, shared_terms=0)

    def seed(self, documents: list[KnowledgeDocument]) -> int:
        if self.count():
            return 0
        return sum(self.add(document) for document in documents)


def build_store(path: Path | str | None = None) -> KnowledgeStore:
    from .pattern_library import SEED_DOCUMENTS

    store = KnowledgeStore(path)
    store.seed(SEED_DOCUMENTS)
    return store


store = build_store()
