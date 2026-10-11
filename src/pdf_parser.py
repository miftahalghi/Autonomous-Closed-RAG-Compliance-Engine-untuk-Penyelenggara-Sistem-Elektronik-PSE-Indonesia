"""
pdf_parser.py – Ekstraksi & pembersihan teks PDF kebijakan privasi.

Pipeline (Step 1 spesifikasi):
  1. Buka PDF via pdfplumber.
  2. Ekstrak teks per halaman.
  3. Normalisasi whitespace, hapus nomor halaman/header/footer.
  4. Deteksi heading/section dokumen.
  5. Kembalikan teks bersih utuh.
"""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber


# ---------------------------------------------------------------------------
# Pembersihan teks
# ---------------------------------------------------------------------------

def _normalize_whitespace(text: str) -> str:
    """Normalisasi whitespace berlebihan tanpa menghilangkan paragraf."""
    # Ganti multiple blank lines dengan satu newline ganda
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Ganti spasi/tab berlebihan dalam satu baris
    text = re.sub(r"[ \t]+", " ", text)
    # Hapus trailing whitespace per baris
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip()


def _remove_page_artifacts(text: str) -> str:
    """Hapus nomor halaman, header/footer umum."""
    # Hapus baris yang hanya berisi angka (nomor halaman)
    text = re.sub(r"^\s*\d{1,3}\s*$", "", text, flags=re.MULTILINE)
    # Hapus pola "Page X of Y" atau "Halaman X dari Y"
    text = re.sub(
        r"(?i)(page|halaman)\s+\d+\s+(of|dari)\s+\d+",
        "",
        text,
    )
    # Hapus pola "- X -" (nomor halaman bergaya)
    text = re.sub(r"^\s*-\s*\d+\s*-\s*$", "", text, flags=re.MULTILINE)
    return text


def _detect_sections(text: str) -> list[dict[str, str]]:
    """
    Deteksi heading/section dalam dokumen kebijakan privasi.

    Mengembalikan list dict {"heading": "...", "content": "..."}.
    Heuristic: baris singkat (<100 char) yang diikuti teks panjang.
    """
    lines = text.split("\n")
    sections: list[dict[str, str]] = []
    current_heading = "Bagian Awal"
    current_content: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_content.append("")
            continue

        # Heuristic deteksi heading:
        # - Singkat (< 100 karakter)
        # - Tidak diakhiri titik
        # - Mengandung huruf kapital dominan ATAU mengandung angka + titik di awal
        is_heading = (
            len(stripped) < 100
            and not stripped.endswith(".")
            and (
                stripped.isupper()
                or stripped.istitle()
                or re.match(r"^\d+[\.\)]\s+", stripped)
                or re.match(r"^[IVXLCDM]+\.\s+", stripped)
                or re.match(r"^Pasal\s+\d+", stripped, re.IGNORECASE)
                or re.match(r"^BAB\s+", stripped, re.IGNORECASE)
                or re.match(r"^(?:Bagian|Bab|Seksi|Section)\s+", stripped, re.IGNORECASE)
            )
        )

        if is_heading and current_content:
            # Simpan section sebelumnya
            content_text = "\n".join(current_content).strip()
            if content_text:
                sections.append({
                    "heading": current_heading,
                    "content": content_text,
                })
            current_heading = stripped
            current_content = []
        else:
            current_content.append(line)

    # Section terakhir
    content_text = "\n".join(current_content).strip()
    if content_text:
        sections.append({
            "heading": current_heading,
            "content": content_text,
        })

    return sections


# ---------------------------------------------------------------------------
# API Publik
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """
    Ekstrak teks bersih dari file PDF (atau TXT sebagai fallback).

    Args:
        pdf_path: Path ke file PDF atau TXT.

    Returns:
        Teks utuh yang sudah dinormalisasi.

    Raises:
        FileNotFoundError: Jika file tidak ditemukan.
        ValueError: Jika file tidak mengandung teks.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"File dokumen tidak ditemukan: {path}")

    # Dukungan file .txt secara langsung untuk pengujian mudah
    if path.suffix.lower() == ".txt":
        full_text = path.read_text(encoding="utf-8")
        full_text = _remove_page_artifacts(full_text)
        full_text = _normalize_whitespace(full_text)
        return full_text

    pages_text: list[str] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    if not pages_text:
        raise ValueError(
            f"PDF tidak mengandung teks yang dapat diekstrak: {path}. "
            "Pastikan PDF bukan berupa scan/gambar."
        )

    # Gabung semua halaman
    full_text = "\n\n".join(pages_text)

    # Bersihkan
    full_text = _remove_page_artifacts(full_text)
    full_text = _normalize_whitespace(full_text)

    return full_text


def parse_pdf_document(pdf_path: str | Path) -> dict:
    """
    Parse dokumen PDF lengkap.

    Returns:
        Dict berisi:
          - "file_name": Nama file.
          - "full_text": Teks utuh bersih.
          - "sections": Daftar section yang terdeteksi.
          - "char_count": Jumlah karakter.
          - "word_count": Estimasi jumlah kata.
    """
    path = Path(pdf_path)
    full_text = extract_text_from_pdf(path)
    sections = _detect_sections(full_text)

    return {
        "file_name": path.name,
        "full_text": full_text,
        "sections": sections,
        "char_count": len(full_text),
        "word_count": len(full_text.split()),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.pdf_parser <path-to-pdf>")
        sys.exit(1)

    result = parse_pdf_document(sys.argv[1])
    print(f"File: {result['file_name']}")
    print(f"Characters: {result['char_count']}")
    print(f"Words: {result['word_count']}")
    print(f"Sections detected: {len(result['sections'])}")
    for s in result["sections"]:
        print(f"  • {s['heading']}")
    print("\n--- Full Text (first 500 chars) ---")
    print(result["full_text"][:500])
