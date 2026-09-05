from signalroom.models import KnowledgeDocument
from signalroom.pattern_library import SEED_DOCUMENTS
from signalroom.retrieval import KnowledgeStore, build_store, split_passages


def fresh_store(tmp_path):
    return build_store(tmp_path / "knowledge.sqlite3")


def test_library_is_seeded_once(tmp_path):
    store = fresh_store(tmp_path)
    seeded = store.count()
    assert seeded == sum(len(split_passages(doc.content)) for doc in SEED_DOCUMENTS)
    assert build_store(tmp_path / "knowledge.sqlite3").count() == seeded


def test_stemming_matches_inflected_terms(tmp_path):
    store = fresh_store(tmp_path)
    hits = store.search("calibrating alerts against historical events and acknowledgements")
    assert hits, "expected the alert design passages to match inflected query terms"
    assert hits[0].title == "Operational alert design"
    assert hits[0].shared_terms >= 2


def test_unrelated_query_returns_nothing(tmp_path):
    store = fresh_store(tmp_path)
    assert store.search("banana smoothie recipe with oat milk") == []


def test_single_common_word_is_not_a_match(tmp_path):
    store = fresh_store(tmp_path)
    assert store.search("pilot") == []


def test_added_document_is_searchable_with_stable_ids(tmp_path):
    store = KnowledgeStore(tmp_path / "empty.sqlite3")
    added = store.add(KnowledgeDocument(
        title="Synthetic safety note",
        content="Every automated decision must retain a reviewable source trail.\n\nA named human reviewer acknowledges each decision before it takes effect.",
    ))
    assert added == 2
    hits = store.search("reviewable source trail for automated decisions")
    assert [hit.passage_id for hit in hits] == ["synthetic-safety-note#1"]
    assert store.get("synthetic-safety-note#2") is not None
    assert store.get("missing#9") is None


def test_ranking_prefers_title_and_term_overlap(tmp_path):
    store = fresh_store(tmp_path)
    hits = store.search("what baseline and acceptance threshold define success for the proof of concept")
    assert hits[0].title == "PoC measurement and baselines"
    assert all(hits[i].score >= hits[i + 1].score for i in range(len(hits) - 1))
