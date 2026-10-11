"""
create_sample_pdf.py – Buat PDF sampel kebijakan privasi untuk pengujian.
Jalankan: python create_sample_pdf.py

Menggunakan pdfplumber-compatible PDF sederhana via reportlab.
Fallback: membuat file TXT jika reportlab tidak tersedia.
"""

import sys
from pathlib import Path

SAMPLE_TEXT = """\
KEBIJAKAN PRIVASI
PT Contoh Digital Indonesia
Berlaku sejak: 1 Januari 2024

1. PENDAHULUAN

PT Contoh Digital Indonesia ("Kami") berkomitmen untuk melindungi privasi pengguna
layanan kami. Kebijakan Privasi ini menjelaskan bagaimana kami mengumpulkan, menggunakan,
menyimpan, dan melindungi Data Pribadi Anda sesuai dengan peraturan perundang-undangan
yang berlaku di Indonesia.

2. DASAR PEMROSESAN DATA

Kami memproses Data Pribadi Anda berdasarkan:
a. Persetujuan eksplisit yang Anda berikan saat mendaftar akun;
b. Pemenuhan kewajiban kontraktual dalam penyediaan layanan;
c. Kewajiban hukum yang berlaku bagi Kami sebagai pengendali data.

Persetujuan Anda bersifat sukarela dan dapat ditarik kembali sewaktu-waktu melalui
pengaturan akun atau dengan menghubungi tim kami.

3. HAK-HAK PENGGUNA

Sebagai Subjek Data Pribadi, Anda memiliki hak untuk:
a. Mengakses dan memperoleh salinan Data Pribadi yang kami proses;
b. Memperbarui atau memperbaiki ketidakakuratan Data Pribadi;
c. Menarik kembali persetujuan pemrosesan Data Pribadi;
d. Mengajukan penghapusan Data Pribadi;
e. Mendapatkan informasi tentang tujuan pemrosesan data;
f. Mengajukan keberatan atas pemrosesan otomatis.

Untuk menjalankan hak-hak tersebut, silakan hubungi Petugas Pelindungan Data kami
di email: dpo@contohdigital.co.id

4. PENGAMANAN DATA

Kami menerapkan langkah-langkah teknis dan operasional untuk melindungi Data Pribadi,
termasuk namun tidak terbatas pada:
a. Enkripsi data saat transit dan saat penyimpanan (at-rest);
b. Pembatasan akses berbasis peran (role-based access control);
c. Pemantauan keamanan berkala dan audit internal;
d. Pelatihan keamanan data untuk seluruh karyawan.

Kami menjaga kerahasiaan Data Pribadi dan memastikan setiap pihak yang memproses data
atas nama kami terikat kewajiban kerahasiaan yang setara.

5. INSIDEN KEAMANAN DATA

Dalam hal terjadi insiden keamanan yang mengakibatkan kebocoran Data Pribadi,
kami akan memberitahukan kepada pengguna yang terdampak dalam waktu yang wajar.
Pemberitahuan tersebut akan mencakup informasi tentang jenis data yang terdampak
dan langkah-langkah penanganan yang dilakukan.

6. PENYIMPANAN DAN PENGHAPUSAN DATA

Data Pribadi Anda akan disimpan selama diperlukan untuk tujuan pemrosesan yang
telah diberitahukan. Setelah tujuan tersebut terpenuhi, kami akan menghapus atau
menganonimkan Data Pribadi Anda sesuai prosedur internal kami.

Anda dapat mengajukan permintaan penghapusan data kapan saja melalui pengaturan
akun atau menghubungi tim dukungan kami.

7. KONTAK

Untuk pertanyaan terkait Kebijakan Privasi ini, hubungi:
Petugas Pelindungan Data (DPO)
Email: dpo@contohdigital.co.id
Telepon: +62-21-1234-5678
Alamat: Jl. Contoh No. 1, Jakarta 12345

Terakhir diperbarui: 1 Januari 2024
"""


def create_sample_pdf_reportlab(output_path: Path):
    """Buat PDF menggunakan reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=8,
    )

    story = []

    for line in SAMPLE_TEXT.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue

        if line.startswith("KEBIJAKAN PRIVASI"):
            story.append(Paragraph(line, title_style))
        elif line[0].isdigit() and "." in line[:3]:
            story.append(Paragraph(line, heading_style))
        else:
            story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)


def create_sample_txt(output_path: Path):
    """Buat file TXT sebagai fallback."""
    output_path = output_path.with_suffix(".txt")
    output_path.write_text(SAMPLE_TEXT, encoding="utf-8")
    return output_path


def main():
    output_dir = Path(__file__).resolve().parent / "data" / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / "sample_policy.pdf"

    try:
        create_sample_pdf_reportlab(pdf_path)
        print(f"✓ Sample PDF created: {pdf_path}")
    except ImportError:
        print("reportlab not installed. Creating TXT fallback...")
        txt_path = create_sample_txt(pdf_path)
        print(f"✓ Sample TXT created: {txt_path}")
        print("  Install reportlab for PDF: pip install reportlab")

    # Juga simpan sebagai TXT untuk testing tanpa pdfplumber
    txt_path = output_dir / "sample_policy.txt"
    txt_path.write_text(SAMPLE_TEXT, encoding="utf-8")
    print(f"✓ Sample TXT also saved: {txt_path}")


if __name__ == "__main__":
    main()
