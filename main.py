"""
main.py – CLI Pipeline Orchestrator untuk Audit Kepatuhan UU PDP.

Menjalankan seluruh pipeline secara linear:
  Step 1: Document Ingestion & Section Parsing
  Step 2: Pillar-Guided Clause Extraction
  Step 3: Targeted Legal Retrieval (Metadata-Boosted Closed RAG)
  Step 4: Strict Grounded Compliance Checker
  Step 5: Aggregation & Report Generation

Usage:
    python main.py <path-to-pdf> [--output <output-json-path>] [--rebuild-index]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Tambahkan root project ke sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PILAR_DEFINITIONS, VECTORDB_DIR
from src.legal_indexer import index_legal_corpus, get_chroma_client, COLLECTION_NAME
from src.pdf_parser import extract_text_from_pdf, parse_pdf_document
from src.clause_extractor import extract_clauses, print_extraction_summary
from src.retriever import (
    LegalRetriever,
    format_retrieved_context,
    print_retrieval_summary,
)
from src.compliance_checker import (
    check_compliance_all,
    print_compliance_summary,
)
from src.reporter import (
    build_audit_report,
    save_report_json,
    print_final_report,
)


def ensure_vector_store(rebuild: bool = False) -> None:
    """Pastikan vector store sudah ada; bangun jika belum atau diminta rebuild."""
    needs_build = rebuild

    if not needs_build:
        try:
            client = get_chroma_client()
            col = client.get_collection(COLLECTION_NAME)
            if col.count() == 0:
                needs_build = True
            else:
                print(f"[Pipeline] Vector store sudah ada ({col.count()} dokumen).")
        except Exception:
            needs_build = True

    if needs_build:
        print("[Pipeline] Membangun vector store dari korpus UU PDP...")
        index_legal_corpus()
        print("[Pipeline] Vector store siap.")


def run_pipeline(
    pdf_path: str | Path,
    output_path: str | Path | None = None,
    rebuild_index: bool = False,
    verbose: bool = True,
) -> dict:
    """
    Jalankan seluruh pipeline audit kepatuhan UU PDP.

    Args:
        pdf_path: Path ke file PDF kebijakan privasi.
        output_path: Path output JSON laporan (opsional).
        rebuild_index: Paksa bangun ulang vector store.
        verbose: Tampilkan output detail.

    Returns:
        Dict berisi report dan metadata pipeline.
    """
    start_time = time.time()

    print("\n" + "=" * 70)
    print("  MESIN AUDIT KEPATUHAN KEBIJAKAN PRIVASI")
    print("  Berbasis Closed-RAG · UU No. 27 Tahun 2022")
    print("=" * 70)

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"\n[ERROR] File tidak ditemukan: {pdf_path}")
        sys.exit(1)

    # -----------------------------------------------------------------
    # Step 0: Pastikan vector store tersedia
    # -----------------------------------------------------------------
    print("\n[Step 0] Memeriksa vector store...")
    ensure_vector_store(rebuild=rebuild_index)

    # -----------------------------------------------------------------
    # Step 1: Document Ingestion & Section Parsing
    # -----------------------------------------------------------------
    print(f"\n[Step 1] Membaca dokumen PDF: {pdf_path.name}...")
    doc_info = parse_pdf_document(pdf_path)
    document_text = doc_info["full_text"]
    document_name = doc_info["file_name"]
    print(f"  Karakter: {doc_info['char_count']:,}")
    print(f"  Kata: {doc_info['word_count']:,}")
    print(f"  Section terdeteksi: {len(doc_info['sections'])}")

    if verbose:
        for s in doc_info["sections"][:10]:
            print(f"    • {s['heading']}")

    # -----------------------------------------------------------------
    # Step 2: Pillar-Guided Clause Extraction
    # -----------------------------------------------------------------
    print("\n[Step 2] Mengekstrak klausul 5 pilar dari dokumen...")
    extraction = extract_clauses(document_text, document_name)

    if verbose:
        print_extraction_summary(extraction)

    # -----------------------------------------------------------------
    # Step 3: Targeted Legal Retrieval
    # -----------------------------------------------------------------
    print("\n[Step 3] Menjalankan retrieval pasal UU PDP...")
    retriever = LegalRetriever()

    # Siapkan query: gunakan raw_text atau deskripsi pilar
    pillar_queries: dict[str, str] = {}
    for pillar in extraction.extracted_pillars:
        pid = pillar.pillar_id
        if pillar.found and pillar.raw_text:
            pillar_queries[pid] = pillar.raw_text
        else:
            # Gunakan deskripsi pilar sebagai fallback query
            pillar_queries[pid] = PILAR_DEFINITIONS.get(pid, {}).get(
                "description", pid,
            )

    retrieved_map = retriever.retrieve_all_pillars(pillar_queries)

    if verbose:
        print_retrieval_summary(retrieved_map)

    # -----------------------------------------------------------------
    # Step 4: Strict Grounded Compliance Checker
    # -----------------------------------------------------------------
    print("\n[Step 4] Mengevaluasi kepatuhan per pilar...")
    compliance_results = check_compliance_all(
        extraction.extracted_pillars,
        retrieved_map,
    )

    if verbose:
        print_compliance_summary(compliance_results)

    # -----------------------------------------------------------------
    # Step 5: Aggregation & Report Generation
    # -----------------------------------------------------------------
    print("\n[Step 5] Menghasilkan laporan audit...")
    report = build_audit_report(document_name, extraction, compliance_results)

    # Simpan JSON
    if output_path is None:
        output_path = PROJECT_ROOT / "audit_report.json"

    json_path = save_report_json(report, output_path)
    print(f"  Laporan JSON disimpan: {json_path}")

    # Tampilkan laporan di terminal
    print_final_report(report)

    elapsed = time.time() - start_time
    print(f"\n[Pipeline] Selesai dalam {elapsed:.1f} detik.")

    return {
        "report": report,
        "json_path": str(json_path),
        "elapsed_seconds": round(elapsed, 1),
    }


def main():
    """Entry point CLI."""
    parser = argparse.ArgumentParser(
        description=(
            "Mesin Audit Kepatuhan Kebijakan Privasi berbasis Closed-RAG "
            "(UU No. 27/2022 tentang Pelindungan Data Pribadi)"
        ),
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path ke file PDF atau TXT kebijakan privasi yang akan diaudit.",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path output file JSON laporan audit (default: audit_report.json).",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Paksa bangun ulang vector store ChromaDB.",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Mode tenang: hanya tampilkan hasil akhir.",
    )

    args = parser.parse_args()

    run_pipeline(
        pdf_path=args.pdf_path,
        output_path=args.output,
        rebuild_index=args.rebuild_index,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
