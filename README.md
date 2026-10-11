# 🛡️ Mesin Audit Kepatuhan Kebijakan Privasi UU No. 27/2022 (UU PDP)
> **Closed-RAG Deterministic Engine for Privacy Policy Compliance Audit**  
> Terintegrasi untuk **Langflow Desktop** & pengembangan **IBM Bob IDE**.

---

## 📌 Ringkasan Solusi & Eliminasi Halusinasi Hukum

Sistem ini dirancang khusus untuk mengaudit dokumen kebijakan privasi organisasi terhadap **Undang-Undang Republik Indonesia Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP)** secara deterministik dan tertutup (*closed-world*).

### Masalah Halusinasi Hukum & Perbaikan Ground Truth
- **Masalah Sebelumnya**: Korpus awal menggunakan naskah **Draf RUU PDP** masa pembahasan di DPR, yang menyebabkan inkonsistensi nomor pasal, ketiadaan dasar pemrosesan data resmi, dan halusinasi norma batas waktu.
- **Perbaikan Resmi**: Korpus `data/raw_legal/uu_27_2022.txt` telah diganti penuh dengan **Naskah Resmi Lembaran Negara Republik Indonesia (LNRI) Tahun 2022 Nomor 196** (Tambahan LNRI Nomor 6820).

---

## ⚖️ 5 Pilar Mandat Kepatuhan Wajib

| ID Pilar | Nama Pilar | Pasal Resmi UU PDP (LNRI 196) | Mandat Hukum Kritis |
| :--- | :--- | :--- | :--- |
| **PILAR_1** | **Dasar Pemrosesan Data** | **Pasal 20 ayat (1) & (2)** | Pengendali wajib memiliki minimal 1 dari 6 dasar pemrosesan sah (persetujuan eksplisit, kontrak, kewajiban hukum, kepentingan vital, tugas publik, atau kepentingan yang sah). |
| **PILAR_2** | **Hak Subjek Data Pribadi** | **Pasal 5 s.d. Pasal 13** | Hak kejelasan informasi (P.5), koreksi (P.6), akses/salinan (P.7), pengakhiran/penghapusan (P.8), penarikan persetujuan (P.9), keberatan pemrofilan otomatis (P.10), pembatasan (P.11), ganti rugi (P.12), dan portabilitas data (P.13). |
| **PILAR_3** | **Kewajiban Pengamanan Data** | **Pasal 35, Pasal 39** | Kewajiban enkripsi, langkah teknis operasional, penentuan tingkat keamanan, dan menjaga kerahasiaan data (berlaku juga bagi Prosesor). |
| **PILAR_4** | **Notifikasi Insiden Kebocoran Data** | **Pasal 46 ayat (1) - (3)** | **Mandat Kritis:** Wajib memberitahukan secara tertulis paling lambat **3 x 24 jam** kepada Subjek Data dan Lembaga Pelindungan Data Pribadi. *(Gating: Jika Nihil/Melanggar = Otomatis `CRITICAL_RISK`)*. |
| **PILAR_5** | **Retensi & Penghapusan Data** | **Pasal 43, Pasal 44** | Syarat wajib penghapusan data (tujuan tercapai, persetujuan dicabut, permintaan subjek) dan pemusnahan dokumen elektronik/fisik. |

---

## 📐 Formula Penilaian & Risk Gating

1. **Formula Skor Kepatuhan Matematis**:
   $$\text{Compliance Score} = \left( \frac{\sum_{i=1}^{5} \text{Weight}(\text{status}_i)}{5 \times 100} \right) \times 100\%$$
   - `COMPLIANT`: **100 poin**
   - `PARTIAL`: **50 poin**
   - `NON_COMPLIANT`: **0 poin**
   - `MISSING`: **0 poin**

2. **Mekanisme Risk Gating**:
   - Jika **PILAR_4** berstatus `NON_COMPLIANT` atau `MISSING` $\rightarrow$ Tingkat risiko keseluruhan terkunci pada **`CRITICAL_RISK`**, mengesampingkan skor pilar lainnya.
   - Selain itu:
     - Skor $< 60\%$ $\rightarrow$ `HIGH_RISK`
     - Skor $60\% - 84\%$ $\rightarrow$ `MEDIUM_RISK`
     - Skor $\ge 85\%$ $\rightarrow$ `LOW_RISK`

---

## 🚀 Panduan Menjalankan di Langflow Desktop

Berkas alur graf telah disiapkan di root repositori: **`audit_pdp_flow.json`**.

### Langkah 1: Impor Flow ke Langflow Desktop
1. Buka aplikasi **Langflow Desktop**.
2. Di halaman Dashboard, klik tombol **"Import"** (atau **"New Flow"** $\rightarrow$ **"Import from JSON"**).
3. Pilih berkas: `audit_pdp_flow.json`.
4. Kanvas visual alur audit Closed-RAG akan terbuka lengkap dengan 7 node yang saling terhubung.

### Langkah 2: Masukkan Google Gemini API Key
1. Pada kanvas Langflow, cari node **`🤖 Google Gemini LLM`**.
2. Pada kolom **`Google API Key`**, tempelkan (*paste*) API key Google Gemini Anda.
3. Konfigurasi model default:
   - Model Name: `gemini-2.0-flash` (atau `gemini-1.5-flash`)
   - Temperature: `0.0` (Wajib 0.0 untuk strict legal reasoning).

### Langkah 3: Jalankan Audit
1. Pada node **`📄 Input Dokumen Privasi`**, teks kebijakan privasi sampel PT Contoh Digital Indonesia telah terpasang secara default.
2. Anda dapat mengganti teks tersebut dengan teks kebijakan privasi organisasi mana pun yang ingin Anda audit.
3. Klik tombol **"Play" (▶)** pada pojok kanan bawah atau buka **Playground / Chat**.
4. Sistem akan mengeksekusi pipeline:
   - `TextInput` $\rightarrow$ `PDP 5-Pillar Clause Extractor` $\rightarrow$ `Targeted Legal Retriever` $\rightarrow$ `Strict Closed-RAG Compliance Checker` $\rightarrow$ `PDP Audit Reporter` $\rightarrow$ `ChatOutput`.
5. Hasil audit lengkap berupa tabel matriks kepatuhan 5 pilar, skor matematis, klasifikasi risiko, gap analysis, dan rekomendasi klausul perbaikan siap-salin akan tampil di antarmuka chat.

---

## 🛠️ Struktur Komponen Kustom Langflow (`src/langflow_components/`)

1. **`clause_extractor_node.py` (`PDPClauseExtractorComponent`)**:
   Mengekstrak klausul relevan untuk 5 pilar ke dalam struktur JSON Pydantic secara verbatim tanpa merombak konteks.
2. **`legal_retriever_node.py` (`PDPLegalRetrieverComponent`)**:
   Menyediakan teks resmi pasal LNRI 196 secara mandiri (*self-contained closed retrieval*) tanpa ketergantungan path disk eksternal.
3. **`compliance_checker_node.py` (`PDPComplianceCheckerComponent`)**:
   Mengevaluasi klausul terhadap pasal resmi secara deterministik (*strict grounding*, dilarang mengutip pasal di luar konteks).
4. **`reporter_node.py` (`PDPAuditReporterComponent`)**:
   Menghitung skor kepatuhan, mengevaluasi *risk gating* Pilar 4, dan memformat laporan dalam Markdown dan JSON.

---

## 💻 Pengembangan di Lingkungan IBM Bob IDE

- Seluruh kode Python di folder `src/` mematuhi standar **Pydantic v2**, *type hints* lengkap, dan *defensive JSON parsing* (`_safe_parse_json`).
- Kode dapat dibuka dan dikembangkan langsung pada editor kode IBM Bob IDE dengan interpreter Python 3.10+.
