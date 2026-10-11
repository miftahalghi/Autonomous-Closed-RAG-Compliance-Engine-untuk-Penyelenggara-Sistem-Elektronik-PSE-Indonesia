"""
legal_indexer.py – Parser korpus UU PDP & indexer ke ChromaDB.

Fungsi utama:
  1. Membaca teks UU 27/2022 dari file.
  2. Memecah teks menjadi chunk per-pasal menggunakan regex deterministik.
  3. Menandai setiap chunk dengan metadata pilar_tags.
  4. Membangun dan menyimpan vector store ChromaDB ke disk.
"""

from __future__ import annotations

import re
from pathlib import Path

import chromadb
from chromadb.config import Settings

from src.config import (
    EMBEDDING_MODEL,
    PASAL_TO_PILAR,
    RAW_LEGAL_DIR,
    UU_PDP_FILE,
    VECTORDB_DIR,
)
from src.schemas import LegalChunk

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------
COLLECTION_NAME = "uu_pdp_27_2022"

# Regex deterministik pemisah pasal (§7 langkah 2)
PASAL_REGEX = re.compile(
    r"(Pasal\s+\d+[\s\S]*?)(?=(?:Pasal\s+\d+\b)|(?:BAB\s+[IVXLCDM]+)|(?:Bagian\s+[A-Za-z]+)|$)",
    re.MULTILINE,
)

# Regex pendeteksi bab aktif
BAB_REGEX = re.compile(
    r"BAB\s+([IVXLCDM]+)\s*\n+\s*(.+)",
    re.MULTILINE,
)

# Regex nomor pasal
PASAL_NUM_REGEX = re.compile(r"Pasal\s+(\d+)")

# Regex ayat
AYAT_REGEX = re.compile(r"\((\d+)\)")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _detect_bab_ranges(text: str) -> list[tuple[int, str, str]]:
    """Deteksi posisi dan info setiap BAB dalam teks."""
    babs: list[tuple[int, str, str]] = []
    for m in BAB_REGEX.finditer(text):
        babs.append((m.start(), m.group(1).strip(), m.group(2).strip()))
    return babs


def _get_bab_for_position(
    pos: int,
    babs: list[tuple[int, str, str]],
) -> tuple[str | None, str | None]:
    """Cari BAB yang menaungi posisi tertentu."""
    current_bab = (None, None)
    for bab_pos, bab_num, bab_title in babs:
        if bab_pos <= pos:
            current_bab = (bab_num, bab_title)
        else:
            break
    return current_bab


def parse_uu_to_chunks(text: str) -> list[LegalChunk]:
    """
    Parse teks UU PDP menjadi daftar LegalChunk.

    Setiap chunk = satu pasal lengkap, dengan metadata:
      - chunk_id, bab, judul_bab, pasal, ayat, pilar_tags, content.
    """
    babs = _detect_bab_ranges(text)
    chunks: list[LegalChunk] = []

    for match in PASAL_REGEX.finditer(text):
        raw_content = match.group(1).strip()
        if not raw_content:
            continue

        # Nomor pasal
        pasal_match = PASAL_NUM_REGEX.search(raw_content)
        if not pasal_match:
            continue
        pasal_num = int(pasal_match.group(1))

        # Deteksi ayat
        ayat_list = sorted(set(int(a) for a in AYAT_REGEX.findall(raw_content)))

        # Deteksi BAB
        bab_num, bab_title = _get_bab_for_position(match.start(), babs)

        # Pilar tags
        pilar_tags = PASAL_TO_PILAR.get(pasal_num, [])

        chunk = LegalChunk(
            chunk_id=f"UU27-2022-PASAL-{pasal_num}",
            bab=bab_num,
            judul_bab=bab_title,
            pasal=pasal_num,
            ayat=ayat_list,
            pilar_tags=pilar_tags,
            content=raw_content,
        )
        chunks.append(chunk)

    return chunks


def load_uu_text(filepath: Path | None = None) -> str:
    """Baca teks UU PDP dari file."""
    path = filepath or UU_PDP_FILE
    if not path.exists():
        raise FileNotFoundError(f"File UU PDP tidak ditemukan: {path}")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# ChromaDB Indexing
# ---------------------------------------------------------------------------

def get_chroma_client() -> chromadb.ClientAPI:
    """Buat/buka ChromaDB client persisten."""
    VECTORDB_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(VECTORDB_DIR),
        settings=Settings(anonymized_telemetry=False),
    )


def build_vector_store(
    chunks: list[LegalChunk],
    client: chromadb.ClientAPI | None = None,
) -> chromadb.Collection:
    """
    Bangun vector store ChromaDB dari daftar LegalChunk.

    Menggunakan embedding model bawaan ChromaDB (all-MiniLM-L6-v2 compatible).
    Jika koleksi sudah ada, akan dihapus dan dibangun ulang.
    """
    if client is None:
        client = get_chroma_client()

    # Hapus koleksi lama jika ada, lalu buat baru
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Korpus UU No. 27 Tahun 2022 tentang PDP"},
    )

    # Batch insert
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for chunk in chunks:
        ids.append(chunk.chunk_id)
        documents.append(chunk.content)
        metadatas.append({
            "bab": chunk.bab or "",
            "judul_bab": chunk.judul_bab or "",
            "pasal": chunk.pasal,
            "ayat": ",".join(str(a) for a in chunk.ayat),
            "pilar_tags": ",".join(chunk.pilar_tags),
        })

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    return collection


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def index_legal_corpus(filepath: Path | None = None) -> tuple[list[LegalChunk], chromadb.Collection]:
    """
    Pipeline lengkap: baca UU → parse → index ke ChromaDB.

    Returns:
        Tuple (daftar chunks, koleksi ChromaDB).
    """
    print("[Legal Indexer] Membaca teks UU PDP...")
    text = load_uu_text(filepath)

    print("[Legal Indexer] Parsing pasal-pasal...")
    chunks = parse_uu_to_chunks(text)
    print(f"[Legal Indexer] Ditemukan {len(chunks)} pasal.")

    # Tampilkan pasal dengan pilar tags
    tagged = [c for c in chunks if c.pilar_tags]
    print(f"[Legal Indexer] {len(tagged)} pasal memiliki pilar tags:")
    for c in tagged:
        print(f"  • Pasal {c.pasal} → {c.pilar_tags}")

    print("[Legal Indexer] Membangun vector store ChromaDB...")
    collection = build_vector_store(chunks)
    print(f"[Legal Indexer] Vector store berhasil dibangun ({collection.count()} dokumen).")

    return chunks, collection


if __name__ == "__main__":
    chunks, collection = index_legal_corpus()
    print("\n✓ Indexing selesai.")
