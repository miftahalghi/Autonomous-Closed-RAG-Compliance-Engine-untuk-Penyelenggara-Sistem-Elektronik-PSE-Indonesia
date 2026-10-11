"""
compliance_checker.py – Evaluator kepatuhan berbasis Closed-RAG.

Step 4 pipeline: Strict Grounded Compliance Checker.
Mengeksekusi LLM Reasoning (Temperature=0.0) untuk mengevaluasi
setiap pilar secara ketat terhadap pasal-pasal UU PDP hasil retrieval.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from google import genai
from google.genai import types

from src.config import (
    GOOGLE_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    PILAR_DEFINITIONS,
)
from src.retriever import RetrievalResult, format_retrieved_context
from src.schemas import (
    ComplianceCheckResult,
    ComplianceStatus,
    ExtractedPillar,
    RiskLevel,
)


# ---------------------------------------------------------------------------
# Prompt template (§5.2)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
Anda adalah Auditor Kepatuhan Hukum Tertutup (Closed Legal Auditor) untuk UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi.

ATURAN STRICT GROUNDING:
1. Anda HANYA BOLEH menggunakan dasar hukum dari [KONTEKS PASAL RESMI] yang disediakan.
2. DILARANG KERAS mengutip pasal atau ayat yang tidak tertulis di dalam [KONTEKS PASAL RESMI].
3. Klasifikasikan status secara objektif:
   - COMPLIANT: Dokumen memenuhi seluruh syarat dan batas waktu yang diwajibkan pasal secara tegas.
   - PARTIAL: Dokumen menyebutkan topik tersebut namun ada syarat penting/batas waktu yang kurang atau ambigu.
   - NON_COMPLIANT: Dokumen secara langsung melanggar atau menafikan hak/kewajiban dalam pasal.
   - MISSING: Dokumen tidak memiliki klausul apapun terkait pilar ini.
4. Tulis rekomendasi klausul perbaikan yang siap disalin oleh tim legal organisasi.
5. Pada field cited_articles, cantumkan HANYA pasal yang benar-benar ada di konteks.
6. Pada field analysis, jelaskan secara detail gap antara klausul dokumen dan kewajiban UU PDP.
7. Pada field risk_level, tentukan tingkat risiko berdasarkan seberapa kritis gap yang ditemukan.

OUTPUT: Kembalikan JSON dengan format ComplianceCheckResult.\
"""

USER_PROMPT_TEMPLATE = """\
PILAR AUDIT: {pillar_id} - {pillar_name}

KLAUSUL DOKUMEN ORGANISASI:
\"\"\"
{raw_clause_text}
\"\"\"

KONTEKS PASAL RESMI UU PDP (GROUND TRUTH):
\"\"\"
{retrieved_articles_text}
\"\"\"
"""

USER_PROMPT_MISSING = """\
PILAR AUDIT: {pillar_id} - {pillar_name}

KLAUSUL DOKUMEN ORGANISASI:
[KLAUSUL TIDAK DITEMUKAN - Pilar ini tidak disebutkan dalam dokumen kebijakan privasi]

KONTEKS PASAL RESMI UU PDP (GROUND TRUTH):
\"\"\"
{retrieved_articles_text}
\"\"\"
"""


# ---------------------------------------------------------------------------
# JSON Schema untuk structured output
# ---------------------------------------------------------------------------

COMPLIANCE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    required=["pillar_id", "status", "analysis", "risk_level"],
    properties={
        "pillar_id": types.Schema(
            type=types.Type.STRING,
            enum=["PILAR_1", "PILAR_2", "PILAR_3", "PILAR_4", "PILAR_5"],
        ),
        "status": types.Schema(
            type=types.Type.STRING,
            enum=["COMPLIANT", "PARTIAL", "NON_COMPLIANT", "MISSING"],
        ),
        "analysis": types.Schema(type=types.Type.STRING),
        "risk_level": types.Schema(
            type=types.Type.STRING,
            enum=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        ),
        "cited_articles": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
        ),
        "suggested_revision": types.Schema(
            type=types.Type.STRING,
            nullable=True,
        ),
    },
)


def _safe_parse_json(text: str) -> dict:
    """Parse JSON secara aman, menangani kemungkinan code fence markdown."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------

def check_compliance_single(
    pillar: ExtractedPillar,
    retrieved_results: list[RetrievalResult],
) -> ComplianceCheckResult:
    """
    Evaluasi kepatuhan satu pilar menggunakan Closed-RAG.

    Args:
        pillar: Hasil ekstraksi pilar dari dokumen.
        retrieved_results: Pasal-pasal UU PDP hasil retrieval.

    Returns:
        ComplianceCheckResult berisi status, analisis, dan rekomendasi.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY belum dikonfigurasi. "
            "Set di file .env atau environment variable."
        )

    pillar_id = pillar.pillar_id
    pillar_name = PILAR_DEFINITIONS.get(pillar_id, {}).get("name", pillar_id)
    retrieved_text = format_retrieved_context(retrieved_results)

    # Jika pilar tidak ditemukan: gunakan prompt MISSING
    if not pillar.found or not pillar.raw_text:
        user_prompt = USER_PROMPT_MISSING.format(
            pillar_id=pillar_id,
            pillar_name=pillar_name,
            retrieved_articles_text=retrieved_text,
        )
    else:
        user_prompt = USER_PROMPT_TEMPLATE.format(
            pillar_id=pillar_id,
            pillar_name=pillar_name,
            raw_clause_text=pillar.raw_text,
            retrieved_articles_text=retrieved_text,
        )

    client = genai.Client(api_key=GOOGLE_API_KEY)

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=[user_prompt],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=LLM_TEMPERATURE,
            response_mime_type="application/json",
            response_schema=COMPLIANCE_SCHEMA,
        ),
    )

    raw_json = _safe_parse_json(response.text)

    # Pastikan pillar_id benar
    raw_json["pillar_id"] = pillar_id

    # Validasi dengan Pydantic
    result = ComplianceCheckResult(**raw_json)

    return result


def check_compliance_all(
    pillars: list[ExtractedPillar],
    retrieved_map: dict[str, list[RetrievalResult]],
) -> list[ComplianceCheckResult]:
    """
    Evaluasi kepatuhan seluruh 5 pilar secara paralel (ThreadPoolExecutor).

    Args:
        pillars: Daftar 5 pilar hasil ekstraksi.
        retrieved_map: Dict {pillar_id: list[RetrievalResult]}.

    Returns:
        List 5 ComplianceCheckResult.
    """
    def _eval_pillar(pillar: ExtractedPillar) -> ComplianceCheckResult:
        pid = pillar.pillar_id
        retrieved = retrieved_map.get(pid, [])
        print(f"  [Compliance Checker] Mengevaluasi {pid} (paralel)...")
        res = check_compliance_single(pillar, retrieved)
        print(f"    ✓ Selesai {pid} -> Status: {res.status.value} | Risk: {res.risk_level.value}")
        return res

    max_workers = min(5, len(pillars)) if pillars else 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_eval_pillar, pillars))

    return results


def print_compliance_summary(results: list[ComplianceCheckResult]) -> None:
    """Cetak ringkasan hasil evaluasi kepatuhan ke terminal."""
    print(f"\n{'='*60}")
    print("HASIL EVALUASI KEPATUHAN")
    print(f"{'='*60}")

    status_icons = {
        ComplianceStatus.COMPLIANT: "✓",
        ComplianceStatus.PARTIAL: "⚠",
        ComplianceStatus.NON_COMPLIANT: "✗",
        ComplianceStatus.MISSING: "○",
    }

    risk_icons = {
        RiskLevel.LOW: "🟢",
        RiskLevel.MEDIUM: "🟡",
        RiskLevel.HIGH: "🟠",
        RiskLevel.CRITICAL: "🔴",
    }

    for r in results:
        pname = PILAR_DEFINITIONS.get(r.pillar_id, {}).get("name", r.pillar_id)
        icon = status_icons.get(r.status, "?")
        risk = risk_icons.get(r.risk_level, "?")

        print(f"\n{icon} [{r.pillar_id}] {pname}")
        print(f"  Status: {r.status.value} | Risiko: {risk} {r.risk_level.value}")
        print(f"  Analisis: {r.analysis[:200]}{'...' if len(r.analysis) > 200 else ''}")
        if r.cited_articles:
            print(f"  Rujukan: {', '.join(r.cited_articles)}")
        if r.suggested_revision:
            print(f"  Rekomendasi: {r.suggested_revision[:200]}{'...' if len(r.suggested_revision) > 200 else ''}")

    print(f"\n{'='*60}")
