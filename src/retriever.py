"""
retriever.py – Metadata-filtered vector search terhadap ChromaDB.

Step 3 pipeline: Targeted Legal Retrieval (Metadata-Boosted Closed RAG).
Untuk setiap pilar yang found=true:
  1. Filter ChromaDB berdasarkan pilar_tags.
  2. Jalankan semantic search berbasis kemiripan teks klausul.
  3. Kembalikan Top-K konteks pasal resmi yang paling relevan.
"""

from __future__ import annotations

import chromadb

from src.config import TOP_K_RETRIEVAL, PILAR_DEFINITIONS
from src.legal_indexer import COLLECTION_NAME, get_chroma_client


# ---------------------------------------------------------------------------
# Tipe hasil retrieval
# ---------------------------------------------------------------------------

class RetrievalResult:
    """Hasil retrieval satu pasal dari vector store."""

    def __init__(
        self,
        chunk_id: str,
        content: str,
        pasal: int,
        pilar_tags: list[str],
        distance: float,
    ):
        self.chunk_id = chunk_id
        self.content = content
        self.pasal = pasal
        self.pilar_tags = pilar_tags
        self.distance = distance

    def __repr__(self) -> str:
        return (
            f"RetrievalResult(chunk_id={self.chunk_id!r}, "
            f"pasal={self.pasal}, distance={self.distance:.4f})"
        )


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------

class LegalRetriever:
    """
    Retriever berbasis metadata-filtered semantic search.

    Menggunakan ChromaDB collection yang sudah terindex oleh legal_indexer.
    """

    def __init__(self, client: chromadb.ClientAPI | None = None):
        self._client = client or get_chroma_client()
        self._collection = self._client.get_collection(COLLECTION_NAME)

    @property
    def collection(self) -> chromadb.Collection:
        return self._collection

    def retrieve_for_pillar(
        self,
        pillar_id: str,
        query_text: str,
        top_k: int = TOP_K_RETRIEVAL,
    ) -> list[RetrievalResult]:
        """
        Retrieve pasal-pasal UU PDP yang relevan untuk satu pilar.

        Args:
            pillar_id: ID pilar (PILAR_1 s.d. PILAR_5).
            query_text: Teks klausul dari dokumen kebijakan privasi.
            top_k: Jumlah hasil teratas.

        Returns:
            List RetrievalResult terurut dari yang paling relevan.
        """
        # Dapatkan daftar nomor pasal yang ditargetkan untuk pilar ini
        pilar_def = PILAR_DEFINITIONS.get(pillar_id, {})
        pasal_numbers = pilar_def.get("pasal_numbers", [])

        # Tentukan jumlah hasil (tidak boleh melebihi jumlah pasal yang ada)
        target_k = top_k
        if pasal_numbers:
            target_k = max(1, min(top_k, len(pasal_numbers)))

        # Buat filter metadata berbasis nomor pasal target
        where_filter = None
        if len(pasal_numbers) == 1:
            where_filter = {"pasal": pasal_numbers[0]}
        elif len(pasal_numbers) > 1:
            where_filter = {"pasal": {"$in": pasal_numbers}}

        results = None
        try:
            if where_filter:
                results = self._collection.query(
                    query_texts=[query_text],
                    n_results=target_k,
                    where=where_filter,
                )
            else:
                results = self._collection.query(
                    query_texts=[query_text],
                    n_results=target_k,
                )
        except Exception:
            # Fallback: jika query dengan filter gagal, query tanpa filter
            try:
                results = self._collection.query(
                    query_texts=[query_text],
                    n_results=min(target_k, self._collection.count()),
                )
            except Exception:
                results = None

        retrieval_results: list[RetrievalResult] = []

        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                content = results["documents"][0][i] if results["documents"] else ""
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0

                pilar_tags = metadata.get("pilar_tags", "").split(",")
                pilar_tags = [t.strip() for t in pilar_tags if t.strip()]

                retrieval_results.append(
                    RetrievalResult(
                        chunk_id=chunk_id,
                        content=content,
                        pasal=int(metadata.get("pasal", 0)),
                        pilar_tags=pilar_tags,
                        distance=distance,
                    )
                )

        return retrieval_results

    def retrieve_all_pillars(
        self,
        pillar_clauses: dict[str, str],
        top_k: int = TOP_K_RETRIEVAL,
    ) -> dict[str, list[RetrievalResult]]:
        """
        Retrieve konteks pasal untuk semua pilar sekaligus.

        Args:
            pillar_clauses: Dict {pillar_id: raw_clause_text}.
            top_k: Jumlah hasil per pilar.

        Returns:
            Dict {pillar_id: list[RetrievalResult]}.
        """
        all_results: dict[str, list[RetrievalResult]] = {}

        for pillar_id, clause_text in pillar_clauses.items():
            results = self.retrieve_for_pillar(pillar_id, clause_text, top_k)
            all_results[pillar_id] = results

        return all_results


def format_retrieved_context(results: list[RetrievalResult]) -> str:
    """
    Format hasil retrieval menjadi teks konteks untuk prompt LLM.

    Returns:
        Teks gabungan pasal-pasal relevan yang siap dimasukkan ke prompt.
    """
    if not results:
        return "[Tidak ada pasal relevan yang ditemukan]"

    parts: list[str] = []
    for r in results:
        parts.append(f"--- {r.chunk_id} (Pasal {r.pasal}) ---\n{r.content}")

    return "\n\n".join(parts)


def print_retrieval_summary(
    all_results: dict[str, list[RetrievalResult]],
) -> None:
    """Cetak ringkasan hasil retrieval ke terminal."""
    print(f"\n{'='*60}")
    print("HASIL RETRIEVAL PASAL UU PDP")
    print(f"{'='*60}")

    for pillar_id, results in all_results.items():
        pname = PILAR_DEFINITIONS.get(pillar_id, {}).get("name", pillar_id)
        print(f"\n[{pillar_id}] {pname}")

        if not results:
            print("  Tidak ada pasal yang di-retrieve.")
            continue

        for r in results:
            print(f"  • Pasal {r.pasal} (distance: {r.distance:.4f})")
            preview = r.content[:150].replace("\n", " ")
            if len(r.content) > 150:
                preview += "..."
            print(f"    {preview}")

    print(f"\n{'='*60}")
