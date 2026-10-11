"""
schemas.py – Kontrak data Pydantic untuk seluruh pipeline audit kepatuhan UU PDP.

Skema yang didefinisikan:
  • LegalChunk          – Metadata satu chunk pasal UU PDP di vector store.
  • ExtractedPillar     – Hasil ekstraksi satu pilar dari dokumen kebijakan privasi.
  • ExtractedClausesOutput – Wrapper seluruh hasil ekstraksi 5 pilar.
  • ComplianceCheckResult – Evaluasi kepatuhan per-pilar.
  • PillarAuditEntry    – Gabungan ekstraksi + evaluasi untuk satu pilar.
  • FinalAuditReport    – Laporan akhir lengkap dengan skor kepatuhan.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerasi
# ---------------------------------------------------------------------------

class PillarID(str, Enum):
    """Identifier 5 pilar wajib UU PDP."""
    PILAR_1 = "PILAR_1"
    PILAR_2 = "PILAR_2"
    PILAR_3 = "PILAR_3"
    PILAR_4 = "PILAR_4"
    PILAR_5 = "PILAR_5"


class ComplianceStatus(str, Enum):
    """Status kepatuhan per pilar."""
    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    NON_COMPLIANT = "NON_COMPLIANT"
    MISSING = "MISSING"


class RiskLevel(str, Enum):
    """Tingkat risiko per pilar."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OverallRiskLevel(str, Enum):
    """Klasifikasi risiko agregat laporan."""
    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL_RISK = "CRITICAL_RISK"


# ---------------------------------------------------------------------------
# 3.1 – Metadata Chunk Regulasi (untuk ChromaDB)
# ---------------------------------------------------------------------------

class LegalChunk(BaseModel):
    """Satu unit pasal/ayat dari UU PDP yang disimpan di vector store."""

    chunk_id: str = Field(
        ...,
        description="ID unik chunk, contoh: 'UU27-2022-PASAL-46'",
        examples=["UU27-2022-PASAL-46"],
    )
    bab: Optional[str] = Field(
        None,
        description="Nomor Bab dalam angka Romawi, contoh: 'IV'",
    )
    judul_bab: Optional[str] = Field(
        None,
        description="Judul Bab, contoh: 'Kewajiban Pengendali Data Pribadi'",
    )
    pasal: int = Field(
        ...,
        description="Nomor pasal",
    )
    ayat: list[int] = Field(
        default_factory=list,
        description="Daftar ayat yang tercakup",
    )
    pilar_tags: list[str] = Field(
        default_factory=list,
        description="Tag pilar terkait, contoh: ['PILAR_4']",
    )
    content: str = Field(
        ...,
        description="Teks lengkap pasal/ayat",
    )


# ---------------------------------------------------------------------------
# 3.2 – Output Ekstraksi Klausul
# ---------------------------------------------------------------------------

class ExtractedPillar(BaseModel):
    """Hasil ekstraksi satu pilar dari dokumen kebijakan privasi."""

    pillar_id: str = Field(
        ...,
        description="ID pilar: PILAR_1 s.d. PILAR_5",
    )
    found: bool = Field(
        ...,
        description="True jika klausul ditemukan dalam dokumen",
    )
    raw_text: Optional[str] = Field(
        None,
        description="Kutipan verbatim dari dokumen. None jika found=false",
    )
    summary: Optional[str] = Field(
        None,
        description="Ringkasan maksud klausul. None jika found=false",
    )
    source_section: Optional[str] = Field(
        None,
        description="Lokasi/sub-judul klausul dalam dokumen",
    )


class ExtractedClausesOutput(BaseModel):
    """Wrapper keseluruhan hasil ekstraksi 5 pilar."""

    document_name: str = Field(
        ...,
        description="Nama file dokumen kebijakan privasi",
    )
    extracted_pillars: list[ExtractedPillar] = Field(
        ...,
        description="Daftar 5 pilar hasil ekstraksi",
        min_length=5,
        max_length=5,
    )


# ---------------------------------------------------------------------------
# 3.3 – Output Evaluasi Kepatuhan Per-Pilar
# ---------------------------------------------------------------------------

class ComplianceCheckResult(BaseModel):
    """Evaluasi kepatuhan satu pilar terhadap pasal UU PDP."""

    pillar_id: str = Field(
        ...,
        description="ID pilar yang dievaluasi",
    )
    status: ComplianceStatus = Field(
        ...,
        description="Status kepatuhan: COMPLIANT / PARTIAL / NON_COMPLIANT / MISSING",
    )
    analysis: str = Field(
        ...,
        description="Analisis gap detail antara klausul dokumen dan pasal UU PDP",
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Tingkat risiko: LOW / MEDIUM / HIGH / CRITICAL",
    )
    cited_articles: list[str] = Field(
        default_factory=list,
        description="Daftar pasal UU PDP yang dirujuk dalam analisis",
    )
    suggested_revision: Optional[str] = Field(
        None,
        description="Rekomendasi revisi klausul yang siap disalin tim legal",
    )


# ---------------------------------------------------------------------------
# 3.4 – Laporan Akhir
# ---------------------------------------------------------------------------

class PillarAuditEntry(BaseModel):
    """Gabungan hasil ekstraksi dan evaluasi untuk satu pilar."""

    pillar_id: str
    pillar_name: str
    found_in_document: bool
    extracted_text: Optional[str] = None
    compliance_status: ComplianceStatus
    risk_level: RiskLevel
    analysis: str
    cited_articles: list[str] = Field(default_factory=list)
    suggested_revision: Optional[str] = None


class FinalAuditReport(BaseModel):
    """Laporan audit akhir lengkap."""

    document_name: str = Field(
        ...,
        description="Nama dokumen kebijakan privasi yang diaudit",
    )
    compliance_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Skor kepatuhan 0-100 berdasarkan formula bobot status",
    )
    overall_risk: OverallRiskLevel = Field(
        ...,
        description="Klasifikasi risiko keseluruhan",
    )
    pillar_results: list[PillarAuditEntry] = Field(
        ...,
        description="Detail audit per pilar",
        min_length=5,
        max_length=5,
    )
    summary: str = Field(
        ...,
        description="Ringkasan eksekutif temuan audit",
    )


# ---------------------------------------------------------------------------
# Utilitas kalkulasi skor
# ---------------------------------------------------------------------------

# Bobot poin per status (sesuai spesifikasi §3.4)
STATUS_WEIGHT: dict[ComplianceStatus, int] = {
    ComplianceStatus.COMPLIANT: 100,
    ComplianceStatus.PARTIAL: 50,
    ComplianceStatus.NON_COMPLIANT: 0,
    ComplianceStatus.MISSING: 0,
}


def calculate_compliance_score(statuses: list[ComplianceStatus]) -> float:
    """
    Hitung skor kepatuhan berdasarkan formula:
      Score = (Σ Weight(status_i) / (5 × 100)) × 100%

    Args:
        statuses: Daftar 5 status kepatuhan pilar.

    Returns:
        Skor kepatuhan dalam persentase (0.0 – 100.0).
    """
    if len(statuses) != 5:
        raise ValueError(f"Dibutuhkan tepat 5 status pilar, diterima {len(statuses)}")

    total_weight = sum(STATUS_WEIGHT[s] for s in statuses)
    score = (total_weight / (5 * 100)) * 100
    return round(score, 2)


def classify_overall_risk(
    score: float,
    pillar_statuses: dict[str, ComplianceStatus],
) -> OverallRiskLevel:
    """
    Klasifikasi tingkat risiko total berdasarkan skor dan status PILAR_4.

    Rules (§3.4):
      • score ≥ 85          → LOW_RISK
      • 60 ≤ score < 85     → MEDIUM_RISK
      • score < 60 OR PILAR_4 = NON_COMPLIANT/MISSING → HIGH_RISK/CRITICAL_RISK
    """
    pilar4_status = pillar_statuses.get("PILAR_4")
    pilar4_critical = pilar4_status in (
        ComplianceStatus.NON_COMPLIANT,
        ComplianceStatus.MISSING,
    )

    if pilar4_critical:
        return OverallRiskLevel.CRITICAL_RISK

    if score < 60:
        return OverallRiskLevel.HIGH_RISK

    if score < 85:
        return OverallRiskLevel.MEDIUM_RISK

    return OverallRiskLevel.LOW_RISK
