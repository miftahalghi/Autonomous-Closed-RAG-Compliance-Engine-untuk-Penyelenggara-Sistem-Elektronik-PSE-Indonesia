"""
test_schemas.py – Unit test untuk validasi skema Pydantic.
Jalankan: python test_schemas.py
"""

import sys
from pathlib import Path

# Tambahkan root project ke sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.schemas import (
    LegalChunk,
    ExtractedPillar,
    ExtractedClausesOutput,
    ComplianceCheckResult,
    FinalAuditReport,
    PillarAuditEntry,
    ComplianceStatus,
    RiskLevel,
    OverallRiskLevel,
    PillarID,
    calculate_compliance_score,
    classify_overall_risk,
    STATUS_WEIGHT,
)


def test_legal_chunk():
    chunk = LegalChunk(
        chunk_id="UU27-2022-PASAL-46",
        bab="IV",
        judul_bab="Kewajiban Pengendali Data Pribadi",
        pasal=46,
        ayat=[1, 2, 3],
        pilar_tags=["PILAR_4"],
        content="Pasal 46\n(1) Dalam hal terjadi kegagalan...",
    )
    assert chunk.chunk_id == "UU27-2022-PASAL-46"
    assert chunk.pasal == 46
    assert chunk.pilar_tags == ["PILAR_4"]
    print("✓ test_legal_chunk passed")


def test_extracted_pillar_found():
    p = ExtractedPillar(
        pillar_id="PILAR_1",
        found=True,
        raw_text="Kami memproses data berdasarkan persetujuan...",
        summary="Klausul menyebut dasar persetujuan.",
        source_section="Bagian 3",
    )
    assert p.found is True
    assert p.raw_text is not None
    print("✓ test_extracted_pillar_found passed")


def test_extracted_pillar_missing():
    p = ExtractedPillar(pillar_id="PILAR_4", found=False, raw_text=None)
    assert p.found is False
    assert p.raw_text is None
    print("✓ test_extracted_pillar_missing passed")


def test_extracted_clauses_output():
    output = ExtractedClausesOutput(
        document_name="test.pdf",
        extracted_pillars=[
            ExtractedPillar(
                pillar_id=f"PILAR_{i}",
                found=i <= 3,
                raw_text="Test" if i <= 3 else None,
            )
            for i in range(1, 6)
        ],
    )
    assert len(output.extracted_pillars) == 5
    assert output.document_name == "test.pdf"
    print("✓ test_extracted_clauses_output passed")


def test_compliance_check_result():
    ccr = ComplianceCheckResult(
        pillar_id="PILAR_4",
        status=ComplianceStatus.PARTIAL,
        analysis="Dokumen menyebutkan notifikasi tetapi tidak spesifik 3x24 jam.",
        risk_level=RiskLevel.HIGH,
        cited_articles=["Pasal 46 ayat (1)", "Pasal 46 ayat (2)"],
        suggested_revision="Tambahkan batas waktu 3x24 jam secara eksplisit.",
    )
    assert ccr.status == ComplianceStatus.PARTIAL
    assert ccr.risk_level == RiskLevel.HIGH
    assert len(ccr.cited_articles) == 2
    print("✓ test_compliance_check_result passed")


def test_calculate_compliance_score():
    # Test: 100+50+100+0+0 = 250/500 = 50%
    statuses = [
        ComplianceStatus.COMPLIANT,
        ComplianceStatus.PARTIAL,
        ComplianceStatus.COMPLIANT,
        ComplianceStatus.NON_COMPLIANT,
        ComplianceStatus.MISSING,
    ]
    score = calculate_compliance_score(statuses)
    assert score == 50.0, f"Expected 50.0, got {score}"

    # Test: all compliant = 100%
    all_compliant = [ComplianceStatus.COMPLIANT] * 5
    assert calculate_compliance_score(all_compliant) == 100.0

    # Test: all missing = 0%
    all_missing = [ComplianceStatus.MISSING] * 5
    assert calculate_compliance_score(all_missing) == 0.0

    # Test: all partial = 50%
    all_partial = [ComplianceStatus.PARTIAL] * 5
    assert calculate_compliance_score(all_partial) == 50.0

    print("✓ test_calculate_compliance_score passed")


def test_classify_overall_risk():
    # PILAR_4 NON_COMPLIANT => always CRITICAL
    risk = classify_overall_risk(
        90.0, {"PILAR_4": ComplianceStatus.NON_COMPLIANT}
    )
    assert risk == OverallRiskLevel.CRITICAL_RISK

    # PILAR_4 MISSING => always CRITICAL
    risk = classify_overall_risk(
        90.0, {"PILAR_4": ComplianceStatus.MISSING}
    )
    assert risk == OverallRiskLevel.CRITICAL_RISK

    # Score >= 85, PILAR_4 OK => LOW_RISK
    risk = classify_overall_risk(
        90.0, {"PILAR_4": ComplianceStatus.COMPLIANT}
    )
    assert risk == OverallRiskLevel.LOW_RISK

    # 60 <= score < 85 => MEDIUM_RISK
    risk = classify_overall_risk(
        70.0, {"PILAR_4": ComplianceStatus.PARTIAL}
    )
    assert risk == OverallRiskLevel.MEDIUM_RISK

    # Score < 60 => HIGH_RISK
    risk = classify_overall_risk(
        40.0, {"PILAR_4": ComplianceStatus.PARTIAL}
    )
    assert risk == OverallRiskLevel.HIGH_RISK

    print("✓ test_classify_overall_risk passed")


def test_final_audit_report():
    report = FinalAuditReport(
        document_name="test.pdf",
        compliance_score=50.0,
        overall_risk=OverallRiskLevel.CRITICAL_RISK,
        pillar_results=[
            PillarAuditEntry(
                pillar_id=f"PILAR_{i}",
                pillar_name=f"Test Pilar {i}",
                found_in_document=True,
                compliance_status=ComplianceStatus.PARTIAL,
                risk_level=RiskLevel.MEDIUM,
                analysis="Test analysis",
            )
            for i in range(1, 6)
        ],
        summary="Test summary.",
    )
    assert report.compliance_score == 50.0
    assert report.overall_risk == OverallRiskLevel.CRITICAL_RISK
    assert len(report.pillar_results) == 5
    print("✓ test_final_audit_report passed")


def main():
    print("=" * 50)
    print("Running Schema Validation Tests")
    print("=" * 50)
    print()

    test_legal_chunk()
    test_extracted_pillar_found()
    test_extracted_pillar_missing()
    test_extracted_clauses_output()
    test_compliance_check_result()
    test_calculate_compliance_score()
    test_classify_overall_risk()
    test_final_audit_report()

    print()
    print("=" * 50)
    print("ALL TESTS PASSED ✓")
    print("=" * 50)


if __name__ == "__main__":
    main()
