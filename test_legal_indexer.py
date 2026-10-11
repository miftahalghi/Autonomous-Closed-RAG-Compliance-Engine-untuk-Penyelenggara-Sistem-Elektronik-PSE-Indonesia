"""
test_legal_indexer.py – Test parser UU PDP dan indexing ChromaDB.
Jalankan: python test_legal_indexer.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import PASAL_TO_PILAR, PILAR_DEFINITIONS
from src.legal_indexer import (
    load_uu_text,
    parse_uu_to_chunks,
    build_vector_store,
    get_chroma_client,
    index_legal_corpus,
    COLLECTION_NAME,
)


def test_load_uu_text():
    text = load_uu_text()
    assert len(text) > 1000, f"UU text too short: {len(text)}"
    assert "Pasal 46" in text, "Pasal 46 not found in text"
    assert "Pasal 20" in text, "Pasal 20 not found in text"
    assert "Pasal 35" in text, "Pasal 35 not found in text"
    print(f"✓ test_load_uu_text: {len(text)} characters loaded")


def test_parse_uu_chunks():
    text = load_uu_text()
    chunks = parse_uu_to_chunks(text)

    assert len(chunks) > 0, "No chunks parsed"
    print(f"  Total chunks parsed: {len(chunks)}")

    # Pastikan pasal-pasal kunci ada
    pasal_nums = {c.pasal for c in chunks}
    key_pasals = [5, 6, 7, 8, 9, 10, 11, 12, 13, 20, 35, 39, 43, 44, 46]
    for p in key_pasals:
        assert p in pasal_nums, f"Pasal {p} not found in parsed chunks"

    # Pastikan pilar_tags benar
    tagged_chunks = [c for c in chunks if c.pilar_tags]
    print(f"  Chunks with pilar tags: {len(tagged_chunks)}")

    for c in tagged_chunks:
        print(f"    Pasal {c.pasal} → {c.pilar_tags}")

    # Verifikasi mapping spesifik
    pasal_map = {c.pasal: c for c in chunks}

    assert "PILAR_1" in pasal_map[20].pilar_tags, "Pasal 20 should have PILAR_1"
    assert "PILAR_3" in pasal_map[35].pilar_tags, "Pasal 35 should have PILAR_3"
    assert "PILAR_3" in pasal_map[39].pilar_tags, "Pasal 39 should have PILAR_3"
    assert "PILAR_4" in pasal_map[46].pilar_tags, "Pasal 46 should have PILAR_4"
    assert "PILAR_5" in pasal_map[43].pilar_tags, "Pasal 43 should have PILAR_5"
    assert "PILAR_5" in pasal_map[44].pilar_tags, "Pasal 44 should have PILAR_5"

    print("✓ test_parse_uu_chunks: all key pasals found with correct tags")


from src.retriever import LegalRetriever, format_retrieved_context


def test_build_vector_store():
    text = load_uu_text()
    chunks = parse_uu_to_chunks(text)

    client = get_chroma_client()
    collection = build_vector_store(chunks, client)

    assert collection.count() == len(chunks), (
        f"Collection count mismatch: {collection.count()} != {len(chunks)}"
    )

    # Test retriever untuk PILAR_4 (Pasal 46)
    retriever = LegalRetriever(client=client)
    results = retriever.retrieve_for_pillar(
        "PILAR_4",
        "kegagalan pelindungan data pribadi pemberitahuan 3 x 24 jam",
        top_k=2,
    )
    assert len(results) > 0, "Query returned no results"
    assert results[0].pasal == 46, f"Expected Pasal 46, got Pasal {results[0].pasal}"
    print(f"  Retriever for PILAR_4 returned: {results[0].chunk_id} (Pasal {results[0].pasal})")

    context_text = format_retrieved_context(results)
    assert "Pasal 46" in context_text
    print(f"  Formatted context length: {len(context_text)} chars")

    print(f"✓ test_build_vector_store: {collection.count()} documents indexed and retrieved successfully")


def test_full_indexing_pipeline():
    chunks, collection = index_legal_corpus()
    assert len(chunks) > 0
    assert collection.count() > 0
    print(f"✓ test_full_indexing_pipeline: {len(chunks)} chunks, {collection.count()} indexed")


def main():
    print("=" * 50)
    print("Running Legal Indexer Tests")
    print("=" * 50)
    print()

    test_load_uu_text()
    print()
    test_parse_uu_chunks()
    print()
    test_build_vector_store()
    print()
    test_full_indexing_pipeline()

    print()
    print("=" * 50)
    print("ALL TESTS PASSED ✓")
    print("=" * 50)


if __name__ == "__main__":
    main()
