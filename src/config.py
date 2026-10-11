"""
config.py – Konfigurasi pusat untuk pipeline audit UU PDP.

Memuat:
  • Path ke direktori data dan vector store.
  • Pemetaan 5 Pilar ke pasal-pasal UU PDP.
  • Konfigurasi model LLM (Google Gemini via google-genai).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_LEGAL_DIR = DATA_DIR / "raw_legal"
SAMPLES_DIR = DATA_DIR / "samples"
VECTORDB_DIR = DATA_DIR / "vectordb"

UU_PDP_FILE = RAW_LEGAL_DIR / "uu_27_2022.txt"

# ---------------------------------------------------------------------------
# Google Gemini API
# ---------------------------------------------------------------------------
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

# Model yang digunakan untuk structured outputs
LLM_MODEL: str = "gemini-2.0-flash"

# Temperature 0.0 untuk determinisme (sesuai spesifikasi)
LLM_TEMPERATURE: float = 0.0

# ---------------------------------------------------------------------------
# Embedding model (untuk ChromaDB + sentence-transformers)
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# Jumlah hasil retrieval per query
TOP_K_RETRIEVAL: int = 2

# ---------------------------------------------------------------------------
# Pemetaan 5 Pilar ke Pasal UU PDP (§2)
# ---------------------------------------------------------------------------

PILAR_DEFINITIONS: dict[str, dict] = {
    "PILAR_1": {
        "name": "Dasar Pemrosesan Data",
        "pasal_mandat": ["Pasal 20 ayat (1)", "Pasal 20 ayat (2)"],
        "pasal_numbers": [20],
        "keywords": [
            "persetujuan eksplisit",
            "dasar yang sah",
            "pemenuhan kewajiban kontrak",
            "kewajiban hukum pengendali",
            "dasar pemrosesan",
            "consent",
        ],
        "description": (
            "Dasar hukum pemrosesan data pribadi: persetujuan eksplisit, "
            "pemenuhan kontrak, kewajiban hukum pengendali."
        ),
    },
    "PILAR_2": {
        "name": "Hak Subjek Data Pribadi",
        "pasal_mandat": [
            "Pasal 5", "Pasal 6", "Pasal 7", "Pasal 8",
            "Pasal 9", "Pasal 10", "Pasal 11", "Pasal 12", "Pasal 13",
        ],
        "pasal_numbers": [5, 6, 7, 8, 9, 10, 11, 12, 13],
        "keywords": [
            "hak akses",
            "hak koreksi",
            "hak menarik persetujuan",
            "hak penghapusan",
            "hak portabilitas",
            "hak subjek data",
        ],
        "description": (
            "Hak-hak subjek data pribadi: akses, koreksi, penarikan "
            "persetujuan, penghapusan/pemusnahan data."
        ),
    },
    "PILAR_3": {
        "name": "Kewajiban Pengamanan & Pengendalian",
        "pasal_mandat": ["Pasal 35", "Pasal 39"],
        "pasal_numbers": [35, 39],
        "keywords": [
            "pengamanan data",
            "perlindungan teknis",
            "akses tidak sah",
            "enkripsi",
            "kerahasiaan",
            "langkah teknis dan operasional",
        ],
        "description": (
            "Kewajiban melindungi data dari akses tidak sah, langkah "
            "teknis & operasional pengamanan, kerahasiaan data."
        ),
    },
    "PILAR_4": {
        "name": "Notifikasi Insiden Kebocoran Data",
        "pasal_mandat": ["Pasal 46 ayat (1)", "Pasal 46 ayat (2)"],
        "pasal_numbers": [46],
        "keywords": [
            "notifikasi kebocoran",
            "pemberitahuan insiden",
            "kegagalan pelindungan",
            "3 x 24 jam",
            "breach notification",
        ],
        "description": (
            "Kewajiban pemberitahuan tertulis maksimal 3×24 jam kepada "
            "Subjek Data dan Lembaga atas insiden kebocoran data."
        ),
    },
    "PILAR_5": {
        "name": "Retensi & Penghapusan Data",
        "pasal_mandat": ["Pasal 43", "Pasal 44"],
        "pasal_numbers": [43, 44],
        "keywords": [
            "retensi data",
            "batas penyimpanan",
            "penghapusan data",
            "pemusnahan data",
            "masa simpan",
            "data retention",
        ],
        "description": (
            "Batas masa simpan data, kewajiban menghapus/memusnahkan "
            "data jika tujuan pemrosesan telah berakhir."
        ),
    },
}

# Reverse mapping: pasal number → list of pilar IDs
PASAL_TO_PILAR: dict[int, list[str]] = {}
for pilar_id, pilar_def in PILAR_DEFINITIONS.items():
    for pasal_num in pilar_def["pasal_numbers"]:
        PASAL_TO_PILAR.setdefault(pasal_num, []).append(pilar_id)
