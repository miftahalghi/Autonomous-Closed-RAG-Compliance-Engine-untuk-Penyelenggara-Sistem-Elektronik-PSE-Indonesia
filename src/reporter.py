"""
reporter.py – Kalkulator skor kepatuhan & generator laporan audit.

Step 5 pipeline: Aggregation & Report Generation.
  1. Hitung skor kepatuhan matematis berdasarkan formula §3.4.
  2. Kompilasi FinalAuditReport (JSON).
  3. Generate tabel ringkasan Markdown untuk terminal.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from tabulate import tabulate

from src.config import PILAR_DEFINITIONS
from src.schemas import (
    ComplianceCheckResult,
    ComplianceStatus,
    ExtractedClausesOutput,
    FinalAuditReport,
    OverallRiskLevel,
    PillarAuditEntry,
    RiskLevel,
    calculate_compliance_score,
    classify_overall_risk,
)


# ---------------------------------------------------------------------------
# Agregasi
# ---------------------------------------------------------------------------

def build_audit_report(
    document_name: str,
    extraction: ExtractedClausesOutput,
    compliance_results: list[ComplianceCheckResult],
) -> FinalAuditReport:
    """
    Bangun laporan audit akhir dari hasil ekstraksi dan evaluasi kepatuhan.

    Args:
        document_name: Nama dokumen yang diaudit.
        extraction: Hasil ekstraksi 5 pilar.
        compliance_results: Hasil evaluasi kepatuhan 5 pilar.

    Returns:
        FinalAuditReport lengkap.
    """
    # Map ekstraksi dan compliance berdasarkan pillar_id
    extraction_map = {p.pillar_id: p for p in extraction.extracted_pillars}
    compliance_map = {r.pillar_id: r for r in compliance_results}

    pillar_entries: list[PillarAuditEntry] = []
    statuses: list[ComplianceStatus] = []
    status_dict: dict[str, ComplianceStatus] = {}

    for pid in ["PILAR_1", "PILAR_2", "PILAR_3", "PILAR_4", "PILAR_5"]:
        ext = extraction_map.get(pid)
        comp = compliance_map.get(pid)

        if comp is None:
            # Fallback jika evaluasi tidak ada
            status = ComplianceStatus.MISSING
            risk = RiskLevel.CRITICAL
            analysis = "Evaluasi tidak tersedia."
            cited = []
            revision = None
        else:
            status = comp.status
            risk = comp.risk_level
            analysis = comp.analysis
            cited = comp.cited_articles
            revision = comp.suggested_revision

        pname = PILAR_DEFINITIONS.get(pid, {}).get("name", pid)
        found = ext.found if ext else False
        raw_text = ext.raw_text if ext else None

        entry = PillarAuditEntry(
            pillar_id=pid,
            pillar_name=pname,
            found_in_document=found,
            extracted_text=raw_text,
            compliance_status=status,
            risk_level=risk,
            analysis=analysis,
            cited_articles=cited,
            suggested_revision=revision,
        )
        pillar_entries.append(entry)
        statuses.append(status)
        status_dict[pid] = status

    # Hitung skor kepatuhan
    score = calculate_compliance_score(statuses)

    # Klasifikasi risiko keseluruhan
    overall_risk = classify_overall_risk(score, status_dict)

    # Generate ringkasan eksekutif
    summary = _generate_executive_summary(
        document_name, score, overall_risk, pillar_entries,
    )

    return FinalAuditReport(
        document_name=document_name,
        compliance_score=score,
        overall_risk=overall_risk,
        pillar_results=pillar_entries,
        summary=summary,
    )


def _generate_executive_summary(
    document_name: str,
    score: float,
    overall_risk: OverallRiskLevel,
    entries: list[PillarAuditEntry],
) -> str:
    """Generate ringkasan eksekutif audit."""
    compliant = sum(1 for e in entries if e.compliance_status == ComplianceStatus.COMPLIANT)
    partial = sum(1 for e in entries if e.compliance_status == ComplianceStatus.PARTIAL)
    non_compliant = sum(1 for e in entries if e.compliance_status == ComplianceStatus.NON_COMPLIANT)
    missing = sum(1 for e in entries if e.compliance_status == ComplianceStatus.MISSING)

    risk_label = overall_risk.value.replace("_", " ")

    lines = [
        f"Dokumen '{document_name}' telah diaudit terhadap 5 pilar wajib UU No. 27/2022 (UU PDP).",
        f"Skor kepatuhan: {score:.1f}% — Klasifikasi risiko: {risk_label}.",
        f"Distribusi status: {compliant} COMPLIANT, {partial} PARTIAL, "
        f"{non_compliant} NON_COMPLIANT, {missing} MISSING.",
    ]

    # Sorot pilar paling kritis
    critical_pillars = [
        e for e in entries
        if e.compliance_status in (ComplianceStatus.NON_COMPLIANT, ComplianceStatus.MISSING)
    ]
    if critical_pillars:
        names = ", ".join(f"{e.pillar_name} ({e.pillar_id})" for e in critical_pillars)
        lines.append(f"Pilar yang memerlukan perhatian segera: {names}.")

    return " ".join(lines)


# ---------------------------------------------------------------------------
# Output: JSON
# ---------------------------------------------------------------------------

def save_report_json(
    report: FinalAuditReport,
    output_path: str | Path,
) -> Path:
    """
    Simpan laporan audit ke file JSON.

    Args:
        report: Laporan audit.
        output_path: Path file output.

    Returns:
        Path file yang disimpan.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = json.loads(report.model_dump_json())
    data["audit_timestamp"] = datetime.now().isoformat()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return path


# ---------------------------------------------------------------------------
# Output: Markdown / Terminal Table
# ---------------------------------------------------------------------------

STATUS_ICONS = {
    ComplianceStatus.COMPLIANT: "✓ COMPLIANT",
    ComplianceStatus.PARTIAL: "⚠ PARTIAL",
    ComplianceStatus.NON_COMPLIANT: "✗ NON_COMPLIANT",
    ComplianceStatus.MISSING: "○ MISSING",
}

RISK_ICONS = {
    RiskLevel.LOW: "🟢 LOW",
    RiskLevel.MEDIUM: "🟡 MEDIUM",
    RiskLevel.HIGH: "🟠 HIGH",
    RiskLevel.CRITICAL: "🔴 CRITICAL",
}

OVERALL_RISK_ICONS = {
    OverallRiskLevel.LOW_RISK: "🟢 LOW RISK",
    OverallRiskLevel.MEDIUM_RISK: "🟡 MEDIUM RISK",
    OverallRiskLevel.HIGH_RISK: "🟠 HIGH RISK",
    OverallRiskLevel.CRITICAL_RISK: "🔴 CRITICAL RISK",
}


def generate_markdown_table(report: FinalAuditReport) -> str:
    """Generate tabel Markdown ringkasan audit."""
    headers = ["Pilar", "Nama", "Ditemukan", "Status", "Risiko"]
    rows = []

    for entry in report.pillar_results:
        rows.append([
            entry.pillar_id,
            entry.pillar_name,
            "Ya" if entry.found_in_document else "Tidak",
            STATUS_ICONS.get(entry.compliance_status, entry.compliance_status.value),
            RISK_ICONS.get(entry.risk_level, entry.risk_level.value),
        ])

    table = tabulate(rows, headers=headers, tablefmt="grid")
    return table


def print_final_report(report: FinalAuditReport) -> None:
    """Cetak laporan audit akhir ke terminal."""
    overall_icon = OVERALL_RISK_ICONS.get(
        report.overall_risk, report.overall_risk.value,
    )

    print("\n" + "=" * 70)
    print("  LAPORAN AUDIT KEPATUHAN KEBIJAKAN PRIVASI")
    print("  UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi")
    print("=" * 70)
    print(f"\n  Dokumen  : {report.document_name}")
    print(f"  Skor     : {report.compliance_score:.1f}%")
    print(f"  Risiko   : {overall_icon}")
    print(f"  Waktu    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n{'─' * 70}")
    print("  MATRIKS AUDIT PER PILAR")
    print(f"{'─' * 70}")

    table = generate_markdown_table(report)
    print(table)

    # Detail per pilar
    print(f"\n{'─' * 70}")
    print("  DETAIL TEMUAN")
    print(f"{'─' * 70}")

    for entry in report.pillar_results:
        status_icon = STATUS_ICONS.get(
            entry.compliance_status, entry.compliance_status.value,
        )
        risk_icon = RISK_ICONS.get(entry.risk_level, entry.risk_level.value)

        print(f"\n  [{entry.pillar_id}] {entry.pillar_name}")
        print(f"  Status: {status_icon} | Risiko: {risk_icon}")
        print(f"  Analisis: {entry.analysis}")
        if entry.cited_articles:
            print(f"  Dasar Hukum: {', '.join(entry.cited_articles)}")
        if entry.suggested_revision:
            print(f"  Rekomendasi Revisi:")
            print(f"    \"{entry.suggested_revision}\"")

    # Ringkasan eksekutif
    print(f"\n{'─' * 70}")
    print("  RINGKASAN EKSEKUTIF")
    print(f"{'─' * 70}")
    print(f"  {report.summary}")
    print(f"\n{'=' * 70}")
