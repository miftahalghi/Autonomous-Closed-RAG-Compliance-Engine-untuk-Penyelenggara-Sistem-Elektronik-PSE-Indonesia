"""
clause_extractor.py – Ekstraksi klausul 5 pilar dari dokumen kebijakan privasi.

Step 2 pipeline: Pillar-Guided Clause Extraction.
Menggunakan LLM (Google Gemini) dengan Structured Output untuk
mengekstrak klausul relevan dari teks dokumen kebijakan privasi
dan memetakannya ke 5 pilar wajib UU PDP.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from google import genai
from google.genai import types

from src.config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, PILAR_DEFINITIONS
from src.schemas import ExtractedClausesOutput, ExtractedPillar


# ---------------------------------------------------------------------------
# Prompt template (§5.1)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
Anda adalah Parser Hukum Khusus Dokumen Kebijakan Privasi.
Tugas Anda: Mengekstrak klausul yang relevan dengan 5 Pilar Wajib UU No. 27/2022 (UU PDP) dari dokumen yang diberikan.

5 PILAR WAJIB:
1. PILAR_1: Dasar Pemrosesan Data (persetujuan eksplisit, dasar kontrak, atau kewajiban hukum).
2. PILAR_2: Hak Subjek Data Pribadi (akses, koreksi, penarikan persetujuan, penghapusan data).
3. PILAR_3: Kewajiban Pengamanan Data (enkripsi, perlindungan teknis terhadap akses tidak sah).
4. PILAR_4: Notifikasi Insiden Kebocoran Data (kewajiban mengabari pengguna jika terjadi insiden keamanan).
5. PILAR_5: Retensi & Penghapusan Data (jangka waktu penyimpanan dan prosedur pemusnahan).

ATURAN EKSTRAKSI:
- Ambil teks asli dari dokumen persis apa adanya (verbatim) pada field raw_text.
- Jika suatu pilar TIDAK DISEBUTKAN sama sekali dalam dokumen, tandai found: false dan raw_text: null.
- Jangan menganalisis kepatuhan pada tahap ini. Tugas Anda HANYA mengekstrak.
- Berikan summary singkat (1-2 kalimat) tentang maksud klausul jika found: true.
- Identifikasi source_section (judul bagian/section) tempat klausul ditemukan.

OUTPUT: Kembalikan JSON dengan format ExtractedClausesOutput yang berisi tepat 5 pilar.\
"""

USER_PROMPT_TEMPLATE = """\
Dokumen Kebijakan Privasi:
\"\"\"
{document_full_text}
\"\"\"
"""


# ---------------------------------------------------------------------------
# JSON Schema untuk structured output
# ---------------------------------------------------------------------------

EXTRACTION_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    required=["document_name", "extracted_pillars"],
    properties={
        "document_name": types.Schema(type=types.Type.STRING),
        "extracted_pillars": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                required=["pillar_id", "found"],
                properties={
                    "pillar_id": types.Schema(
                        type=types.Type.STRING,
                        enum=["PILAR_1", "PILAR_2", "PILAR_3", "PILAR_4", "PILAR_5"],
                    ),
                    "found": types.Schema(type=types.Type.BOOLEAN),
                    "raw_text": types.Schema(type=types.Type.STRING, nullable=True),
                    "summary": types.Schema(type=types.Type.STRING, nullable=True),
                    "source_section": types.Schema(type=types.Type.STRING, nullable=True),
                },
            ),
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
# Ekstraktor
# ---------------------------------------------------------------------------

PILLAR_SPECS = [
    {
        "id": "PILAR_1",
        "name": "Dasar Pemrosesan Data",
        "desc": "Klausul tentang dasar hukum pemrosesan data, persetujuan eksplisit pengguna, pelaksanaan kontrak, atau kewajiban hukum (Pasal 20 UU PDP)."
    },
    {
        "id": "PILAR_2",
        "name": "Hak Subjek Data Pribadi",
        "desc": "Klausul tentang hak-hak pengguna sebagai subjek data: hak akses, perbaikan/koreksi, penarikan persetujuan, penghapusan, ganti rugi, atau keberatan (Pasal 5 s.d. 13 UU PDP)."
    },
    {
        "id": "PILAR_3",
        "name": "Kewajiban Pengamanan Data",
        "desc": "Klausul tentang langkah teknis dan operasional perlindungan data, enkripsi data saat transit dan penyimpanan (at-rest), serta kontrol akses (Pasal 35 & 39 UU PDP)."
    },
    {
        "id": "PILAR_4",
        "name": "Notifikasi Insiden Kebocoran Data",
        "desc": "Klausul tentang kewajiban dan batas waktu pemberitahuan tertulis jika terjadi insiden keamanan atau kegagalan perlindungan data pribadi (Pasal 46 UU PDP)."
    },
    {
        "id": "PILAR_5",
        "name": "Retensi & Penghapusan Data",
        "desc": "Klausul tentang masa retensi/jangka waktu penyimpanan data pribadi serta prosedur dan jadwal penghapusan atau pemusnahan data (Pasal 43 & 44 UU PDP)."
    }
]


def extract_clauses(
    document_text: str,
    document_name: str = "unknown",
) -> ExtractedClausesOutput:
    """
    Ekstrak klausul 5 pilar dari teks dokumen kebijakan privasi secara paralel.

    Args:
        document_text: Teks lengkap dokumen kebijakan privasi.
        document_name: Nama file dokumen.

    Returns:
        ExtractedClausesOutput berisi 5 pilar dengan status found dan raw_text.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY belum dikonfigurasi. "
            "Set di file .env atau environment variable."
        )

    client = genai.Client(api_key=GOOGLE_API_KEY)
    sample_doc = document_text[:50000]

    def _extract_single_pillar(spec: dict) -> ExtractedPillar:
        pid = spec["id"]
        pname = spec["name"]
        pdesc = spec["desc"]

        prompt = (
            "Anda adalah Parser Hukum Dokumen Kebijakan Privasi untuk UU No. 27/2022 (UU PDP).\n"
            f"Tugas: Ekstrak klausul yang relevan dengan pilar {pid} ({pname}) dari dokumen kebijakan privasi berikut.\n\n"
            f"DESKRIPSI PILAR:\n{pdesc}\n\n"
            "DOKUMEN KEBIJAKAN PRIVASI:\n"
            f"```\n{sample_doc}\n```\n\n"
            "ATURAN EKSTRAKSI:\n"
            "1. Jika klausul pilar ini DITEMUKAN dalam dokumen:\n"
            "   - set found: true\n"
            "   - set raw_text: kutipan teks asli persis dari dokumen (verbatim)\n"
            "   - set summary: ringkasan 1-2 kalimat tentang maksud klausul\n"
            "   - set source_section: nama/nomor bagian tempat klausul ditemukan (misal: '2. DASAR PEMROSESAN DATA')\n"
            "2. Jika pilar ini TIDAK DISEBUTKAN sama sekali dalam dokumen:\n"
            "   - set found: false\n"
            "   - set raw_text: null\n"
            "   - set summary: null\n"
            "   - set source_section: null\n\n"
            "Kembalikan HANYA format JSON valid:\n"
            "```json\n"
            "{\n"
            f'  "pillar_id": "{pid}",\n'
            '  "found": true,\n'
            '  "raw_text": "...",\n'
            '  "summary": "...",\n'
            '  "source_section": "..."\n'
            "}\n"
            "```"
        )

        try:
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=LLM_TEMPERATURE,
                    response_mime_type="application/json",
                ),
            )
            parsed = _safe_parse_json(response.text)
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                parsed = parsed[0]
            elif not isinstance(parsed, dict):
                parsed = {}
        except Exception:
            parsed = {}

        is_found = bool(parsed.get("found", False))
        raw_t = parsed.get("raw_text")
        return ExtractedPillar(
            pillar_id=pid,
            found=is_found,
            raw_text=str(raw_t) if (is_found and raw_t) else None,
            summary=str(parsed.get("summary")) if (is_found and parsed.get("summary")) else None,
            source_section=str(parsed.get("source_section")) if (is_found and parsed.get("source_section")) else None,
        )

    with ThreadPoolExecutor(max_workers=5) as executor:
        extracted_pillars = list(executor.map(_extract_single_pillar, PILLAR_SPECS))

    return ExtractedClausesOutput(
        document_name=document_name,
        extracted_pillars=extracted_pillars,
    )


def print_extraction_summary(result: ExtractedClausesOutput) -> None:
    """Cetak ringkasan hasil ekstraksi ke terminal."""
    print(f"\n{'='*60}")
    print(f"HASIL EKSTRAKSI KLAUSUL: {result.document_name}")
    print(f"{'='*60}")

    for pillar in result.extracted_pillars:
        pid = pillar.pillar_id
        pname = PILAR_DEFINITIONS.get(pid, {}).get("name", pid)
        status = "✓ DITEMUKAN" if pillar.found else "✗ TIDAK DITEMUKAN"

        print(f"\n[{pid}] {pname}")
        print(f"  Status: {status}")

        if pillar.found:
            if pillar.source_section:
                print(f"  Lokasi: {pillar.source_section}")
            if pillar.summary:
                print(f"  Ringkasan: {pillar.summary}")
            if pillar.raw_text:
                preview = pillar.raw_text[:200]
                if len(pillar.raw_text) > 200:
                    preview += "..."
                print(f"  Kutipan: {preview}")

    print(f"\n{'='*60}")
    found_count = sum(1 for p in result.extracted_pillars if p.found)
    print(f"Total: {found_count}/5 pilar ditemukan dalam dokumen.")
    print(f"{'='*60}")
