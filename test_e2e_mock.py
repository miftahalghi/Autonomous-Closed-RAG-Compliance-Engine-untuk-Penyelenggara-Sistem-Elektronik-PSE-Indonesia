"""
test_e2e_mock.py – Test integrasi end-to-end pipeline tanpa membutuhkan API key.

Menguji:
  1. PDF/TXT Parser: ekstraksi dan deteksi section dari dokumen sampel.
  2. Legal Indexer: parsing korpus UU PDP dan indexing ke ChromaDB.
  3. Retriever: targeted retrieval untuk 5 pilar dengan metadata filtering.
  4. Evaluator (Mock LLM response): validasi skema ComplianceCheckResult.
  5. Reporter: kalkulasi skor kepatuhan, klasifikasi risiko, ekspor JSON, dan tabel Markdown.
"""

import json
import sys
from pathlib import Path

# Tambahkan root project ke sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PILAR_DEFINITIONS, SAMPLES_DIR
from src.legal_indexer import index_legal_corpus
from src.pdf_parser import parse_pdf_document
from src.retriever import LegalRetriever, format_retrieved_context
from src.schemas import (
    ComplianceCheckResult,
    ComplianceStatus,
    ExtractedClausesOutput,
    ExtractedPillar,
    RiskLevel,
)
from src.reporter import build_audit_report, save_report_json, print_final_report


def main():
    print("=" * 70)
    print("  TEST INTEGRASI END-TO-END (MOCK LLM)")
    print("=" * 70)

    # -------------------------------------------------------------
    # Step 1: Parse Dokumen Sampel
    # -------------------------------------------------------------
    sample_file = SAMPLES_DIR / "sample_policy.txt"
    print(f"\n[Step 1] Membaca dokumen sampel: {sample_file.name}...")
    doc_info = parse_pdf_document(sample_file)
    print(f"  ✓ Karakter: {doc_info['char_count']}")
    print(f"  ✓ Kata: {doc_info['word_count']}")
    print(f"  ✓ Section terdeteksi: {len(doc_info['sections'])}")
    for s in doc_info["sections"]:
        print(f"    • {s['heading']}")

    # -------------------------------------------------------------
    # Step 2: Index Korpus UU PDP
    # -------------------------------------------------------------
    print("\n[Step 2] Indexing Korpus UU PDP ke ChromaDB...")
    chunks, collection = index_legal_corpus()
    print(f"  ✓ {len(chunks)} pasal terurai, {collection.count()} terindeks di vector store.")

    # -------------------------------------------------------------
    # Step 3: Mock Ekstraksi Klausul (sesuai isi sample_policy.txt)
    # -------------------------------------------------------------
    print("\n[Step 3] Memvalidasi Ekstraksi Klausul 5 Pilar...")
    mock_extraction = ExtractedClausesOutput(
        document_name=doc_info["file_name"],
        extracted_pillars=[
            ExtractedPillar(
                pillar_id="PILAR_1",
                found=True,
                raw_text="Kami memproses Data Pribadi Anda berdasarkan: a. Persetujuan eksplisit yang Anda berikan saat mendaftar akun; b. Pemenuhan kewajiban kontraktual...",
                summary="Pemrosesan didasarkan pada persetujuan eksplisit, kontrak, dan kewajiban hukum.",
                source_section="2. DASAR PEMROSESAN DATA",
            ),
            ExtractedPillar(
                pillar_id="PILAR_2",
                found=True,
                raw_text="Sebagai Subjek Data Pribadi, Anda memiliki hak untuk: a. Mengakses dan memperoleh salinan... b. Memperbarui atau memperbaiki... c. Menarik kembali persetujuan...",
                summary="Menyediakan hak akses, koreksi, penarikan persetujuan, dan penghapusan.",
                source_section="3. HAK-HAK PENGGUNA",
            ),
            ExtractedPillar(
                pillar_id="PILAR_3",
                found=True,
                raw_text="Kami menerapkan langkah-langkah teknis dan operasional untuk melindungi Data Pribadi, termasuk enkripsi saat transit dan at-rest, RBAC, dan audit internal.",
                summary="Penerapan enkripsi, kontrol akses berbasis peran, dan audit keamanan berkala.",
                source_section="4. PENGAMANAN DATA",
            ),
            ExtractedPillar(
                pillar_id="PILAR_4",
                found=True,
                raw_text="Dalam hal terjadi insiden keamanan yang mengakibatkan kebocoran Data Pribadi, kami akan memberitahukan kepada pengguna yang terdampak dalam waktu yang wajar.",
                summary="Notifikasi insiden keamanan dijanjikan dalam waktu yang wajar.",
                source_section="5. INSIDEN KEAMANAN DATA",
            ),
            ExtractedPillar(
                pillar_id="PILAR_5",
                found=True,
                raw_text="Data Pribadi Anda akan disimpan selama diperlukan untuk tujuan pemrosesan yang telah diberitahukan. Setelah tujuan tersebut terpenuhi, kami akan menghapus atau menganonimkan...",
                summary="Penyimpanan data dibatasi selama diperlukan, dihapus setelah tujuan berakhir.",
                source_section="6. PENYIMPANAN DAN PENGHAPUSAN DATA",
            ),
        ],
    )
    print(f"  ✓ {len(mock_extraction.extracted_pillars)} pilar tervalidasi via Pydantic.")

    # -------------------------------------------------------------
    # Step 4: Targeted Legal Retrieval
    # -------------------------------------------------------------
    print("\n[Step 4] Menjalankan Targeted Legal Retrieval...")
    retriever = LegalRetriever()
    for p in mock_extraction.extracted_pillars:
        results = retriever.retrieve_for_pillar(p.pillar_id, p.raw_text, top_k=2)
        print(f"  • [{p.pillar_id}] retrieved {len(results)} pasal:")
        for r in results:
            print(f"    - Pasal {r.pasal} (dist: {r.distance:.4f})")
        ctx = format_retrieved_context(results)
        assert len(ctx) > 50, f"Context too short for {p.pillar_id}"

    # -------------------------------------------------------------
    # Step 5: Mock Compliance Evaluation
    # -------------------------------------------------------------
    print("\n[Step 5] Evaluasi Kepatuhan (Closed-RAG Reasoning)...")
    mock_compliance_results = [
        ComplianceCheckResult(
            pillar_id="PILAR_1",
            status=ComplianceStatus.COMPLIANT,
            analysis="Dokumen telah mencantumkan dasar pemrosesan berupa persetujuan eksplisit, pemenuhan kontrak, dan kewajiban hukum sesuai Pasal 20 ayat (2) UU PDP.",
            risk_level=RiskLevel.LOW,
            cited_articles=["Pasal 20 ayat (1)", "Pasal 20 ayat (2)"],
            suggested_revision=None,
        ),
        ComplianceCheckResult(
            pillar_id="PILAR_2",
            status=ComplianceStatus.COMPLIANT,
            analysis="Dokumen mencantumkan hak akses, perbaikan, penarikan persetujuan, dan penghapusan data secara komprehensif sesuai Pasal 5 s.d. Pasal 13 UU PDP.",
            risk_level=RiskLevel.LOW,
            cited_articles=["Pasal 5", "Pasal 6", "Pasal 7", "Pasal 8", "Pasal 9"],
            suggested_revision=None,
        ),
        ComplianceCheckResult(
            pillar_id="PILAR_3",
            status=ComplianceStatus.COMPLIANT,
            analysis="Dokumen menjelaskan langkah teknis operasional (enkripsi, RBAC, audit) dan kerahasiaan data sesuai mandat Pasal 35 dan Pasal 39 UU PDP.",
            risk_level=RiskLevel.LOW,
            cited_articles=["Pasal 35 ayat (1)", "Pasal 39 ayat (1)"],
            suggested_revision=None,
        ),
        ComplianceCheckResult(
            pillar_id="PILAR_4",
            status=ComplianceStatus.PARTIAL,
            analysis="Dokumen menjanjikan notifikasi kebocoran namun menggunakan frasa 'dalam waktu yang wajar', bertentangan dengan batas tegas UU PDP Pasal 46 ayat (1) yaitu paling lambat 3 x 24 jam, serta belum menyebutkan kewajiban notifikasi tertulis kepada Lembaga.",
            risk_level=RiskLevel.HIGH,
            cited_articles=["Pasal 46 ayat (1)", "Pasal 46 ayat (2)"],
            suggested_revision="Tambahkan klausul eksplisit: 'Pemberitahuan tertulis atas insiden kegagalan perlindungan data akan disampaikan kepada Subjek Data dan Lembaga paling lambat 3 x 24 jam.'",
        ),
        ComplianceCheckResult(
            pillar_id="PILAR_5",
            status=ComplianceStatus.COMPLIANT,
            analysis="Dokumen memuat kewajiban penghapusan data saat tujuan tercapai dan atas permintaan pengguna, selaras dengan Pasal 43 dan Pasal 44 UU PDP.",
            risk_level=RiskLevel.LOW,
            cited_articles=["Pasal 43", "Pasal 44"],
            suggested_revision=None,
        ),
    ]

    # -------------------------------------------------------------
    # Step 6: Kalkulasi Skor & Pelaporan
    # -------------------------------------------------------------
    print("\n[Step 6] Agregasi Laporan & Perhitungan Skor Matematis...")
    report = build_audit_report(
        document_name=doc_info["file_name"],
        extraction=mock_extraction,
        compliance_results=mock_compliance_results,
    )

    # 4 Compliant (100) + 1 Partial (50) = 450 / 500 * 100 = 90.0%
    print(f"  ✓ Compliance Score: {report.compliance_score}% (Expected: 90.0%)")
    assert report.compliance_score == 90.0
    print(f"  ✓ Overall Risk: {report.overall_risk.value}")

    # Simpan JSON
    json_path = PROJECT_ROOT / "test_audit_report.json"
    save_report_json(report, json_path)
    print(f"  ✓ Laporan JSON berhasil disimpan di: {json_path}")

    # Cetak laporan terminal
    print_final_report(report)

    print("\n" + "=" * 70)
    print("  SELURUH INTEGRASI PIPELINE TERVALIDASI DENGAN SUKSES ✓")
    print("=" * 70)


if __name__ == "__main__":
    main()
