export const MOCK_RESULT = {
  document_name: "Sample_Policy_PT_Contoh_Digital.pdf",
  compliance_score: 50.0,
  overall_risk: "KRITIS",
  summary:
    "Dokumen memiliki kelemahan hukum fatal pada Pilar 4 (Notifikasi Insiden Kebocoran Data) karena hanya menyatakan 'waktu yang wajar' tanpa mencantumkan batas waktu wajib 3 x 24 jam sebagaimana dimandatkan Pasal 46 UU PDP. Dua pilar lainnya (Pilar 2 & Pilar 5) berstatus PARTIAL dan memerlukan revisi substansial. Secara keseluruhan, dokumen ini belum memenuhi standar minimum kepatuhan UU PDP dan memerlukan revisi menyeluruh sebelum dapat digunakan secara hukum.",
  pillar_results: [
    {
      pillar_id: "PILAR_1",
      pillar_name: "Dasar Pemrosesan Data",
      found_in_document: true,
      extracted_text:
        "Kami memproses Data Pribadi Anda berdasarkan: a. Persetujuan eksplisit yang Anda berikan kepada kami; b. Pemenuhan kewajiban kontraktual antara Anda dan PT Contoh Digital; c. Kewajiban hukum yang berlaku di Republik Indonesia.",
      compliance_status: "COMPLIANT",
      risk_level: "LOW",
      analysis:
        "Dokumen secara eksplisit mencantumkan tiga dasar pemrosesan data yang sah: persetujuan eksplisit, pemenuhan kewajiban kontrak, dan kepatuhan hukum. Ketiga dasar ini sesuai dengan ketentuan Pasal 20 UU PDP yang mensyaratkan dasar hukum yang jelas untuk setiap kegiatan pemrosesan data pribadi.",
      cited_articles: ["Pasal 20 ayat (1)", "Pasal 20 ayat (2)"],
      suggested_revision: null,
    },
    {
      pillar_id: "PILAR_2",
      pillar_name: "Hak Subjek Data Pribadi",
      found_in_document: true,
      extracted_text:
        "Sebagai Subjek Data Pribadi, Anda memiliki hak untuk: a. Mengakses Data Pribadi Anda yang kami kelola; b. Memperbarui atau memperbaiki Data Pribadi yang tidak akurat; c. Menarik kembali persetujuan pemrosesan data kapan saja.",
      compliance_status: "PARTIAL",
      risk_level: "MEDIUM",
      analysis:
        "Hak dasar sudah disebutkan, namun belum mencantumkan hak ganti rugi atas pelanggaran data (Pasal 12) dan hak transfer data portabilitas (Pasal 13). Ketiadaan dua hak fundamental ini menjadikan dokumen tidak memenuhi standar minimum Pasal 5 s.d. 13 UU PDP.",
      cited_articles: ["Pasal 5 s.d. 13 UU PDP"],
      suggested_revision:
        "Tambahkan poin berikut pada klausul hak subjek data: 'g. Memperoleh dan/atau menggunakan Data Pribadi Anda dalam format yang umum digunakan dan dapat dibaca oleh perangkat elektronik (portabilitas data) sebagaimana diatur dalam Pasal 13 UU PDP; h. Mengajukan tuntutan ganti rugi atas kerugian yang timbul akibat pelanggaran pemrosesan Data Pribadi Anda sesuai ketentuan Pasal 12 UU PDP.'",
    },
    {
      pillar_id: "PILAR_3",
      pillar_name: "Kewajiban Pengamanan & Pengendalian",
      found_in_document: true,
      extracted_text:
        "Kami menerapkan langkah-langkah teknis dan operasional untuk melindungi Data Pribadi, termasuk enkripsi data saat transit dan saat disimpan (at-rest), serta penerapan kontrol akses berbasis peran.",
      compliance_status: "COMPLIANT",
      risk_level: "LOW",
      analysis:
        "Klausul telah mencantumkan mekanisme enkripsi in-transit dan at-rest serta kontrol akses berbasis peran. Pengamanan ini sesuai dengan standar teknis Pasal 35 & 39 UU PDP yang mewajibkan Pengendali Data untuk menerapkan langkah-langkah keamanan yang proporsional.",
      cited_articles: ["Pasal 35", "Pasal 39"],
      suggested_revision: null,
    },
    {
      pillar_id: "PILAR_4",
      pillar_name: "Notifikasi Insiden Kebocoran Data",
      found_in_document: true,
      extracted_text:
        "Dalam hal terjadi insiden keamanan yang mengakibatkan kebocoran Data Pribadi, kami akan memberitahukan kepada pengguna yang terdampak dalam waktu yang wajar.",
      compliance_status: "NON_COMPLIANT",
      risk_level: "CRITICAL",
      analysis:
        "PELANGGARAN HUKUM FATAL: Frasa 'dalam waktu yang wajar' secara tegas melanggar ketentuan Pasal 46 UU PDP yang mewajibkan pemberitahuan tertulis paling lambat 3 x 24 jam terhitung sejak terjadinya kegagalan pelindungan data, baik kepada Subjek Data Pribadi maupun kepada Lembaga Pelindungan Data Pribadi resmi. Penggunaan frasa yang ambigu ini berpotensi menimbulkan sanksi administratif dan pidana.",
      cited_articles: ["Pasal 46 ayat (1)", "Pasal 46 ayat (2)", "Pasal 46 ayat (3)"],
      suggested_revision:
        "Dalam hal terjadi kegagalan pelindungan Data Pribadi, Kami wajib menyampaikan pemberitahuan tertulis paling lambat 3 x 24 (tiga kali dua puluh empat) jam terhitung sejak terjadinya kegagalan tersebut kepada: (i) Subjek Data Pribadi yang terdampak, memuat uraian data yang bocor, dampak yang ditimbulkan, dan langkah mitigasi yang telah diambil; serta (ii) Lembaga Pelindungan Data Pribadi Republik Indonesia sebagaimana ditetapkan oleh Pemerintah.",
    },
    {
      pillar_id: "PILAR_5",
      pillar_name: "Retensi & Penghapusan Data",
      found_in_document: true,
      extracted_text:
        "Data Pribadi Anda akan disimpan selama diperlukan untuk tujuan pemrosesan yang telah diberitahukan. Setelah tujuan tersebut terpenuhi, kami akan menghapus Data Pribadi Anda sesuai prosedur internal kami.",
      compliance_status: "PARTIAL",
      risk_level: "MEDIUM",
      analysis:
        "Dokumen menyebutkan penghapusan data pasca-pemenuhan tujuan, namun tidak menyebutkan batas waktu retensi yang spesifik dalam satuan waktu terukur, tidak menyebutkan prosedur pemusnahan permanen yang dapat diverifikasi, dan tidak mengatur mekanisme penghapusan jika subjek data menarik persetujuan (Pasal 43 & 44 UU PDP).",
      cited_articles: ["Pasal 43", "Pasal 44"],
      suggested_revision:
        "Kami menyimpan Data Pribadi Anda selama masa aktif layanan ditambah 5 (lima) tahun sesuai ketentuan retensi minimum perundang-undangan yang berlaku, dan akan menghapus serta memusnahkan data tersebut secara permanen apabila: (i) tujuan pemrosesan telah berakhir; (ii) masa retensi wajib telah terlampaui; atau (iii) Anda mengajukan permohonan penarikan persetujuan sebagaimana diatur dalam Pasal 43 dan Pasal 44 UU PDP.",
    },
  ],
};

export const SAMPLE_POLICIES = {
  critical: {
    document_name: "Kebijakan_Privasi_PT_Contoh_Digital.pdf",
    document_text: `KEBIJAKAN PRIVASI PT CONTOH DIGITAL

1. DASAR PEMROSESAN DATA
Kami memproses Data Pribadi Anda berdasarkan: a. Persetujuan eksplisit yang Anda berikan kepada kami; b. Pemenuhan kewajiban kontraktual antara Anda dan PT Contoh Digital; c. Kewajiban hukum yang berlaku di Republik Indonesia.

2. HAK SUBJEK DATA PRIBADI
Sebagai Subjek Data Pribadi, Anda memiliki hak untuk: a. Mengakses Data Pribadi Anda yang kami kelola; b. Memperbarui atau memperbaiki Data Pribadi yang tidak akurat; c. Menarik kembali persetujuan pemrosesan data kapan saja.

3. KEAMANAN DATA
Kami menerapkan langkah-langkah teknis dan operasional untuk melindungi Data Pribadi, termasuk enkripsi data saat transit dan saat disimpan (at-rest), serta penerapan kontrol akses berbasis peran.

4. NOTIFIKASI INSIDEN
Dalam hal terjadi insiden keamanan yang mengakibatkan kebocoran Data Pribadi, kami akan memberitahukan kepada pengguna yang terdampak dalam waktu yang wajar.

5. RETENSI DATA
Data Pribadi Anda akan disimpan selama diperlukan untuk tujuan pemrosesan yang telah diberitahukan. Setelah tujuan tersebut terpenuhi, kami akan menghapus Data Pribadi Anda sesuai prosedur internal kami.`,
  },
  compliant: {
    document_name: "Kebijakan_Privasi_Compliant_Corp.pdf",
    document_text: `KEBIJAKAN PRIVASI COMPLIANT CORP

1. DASAR PEMROSESAN DATA (Pasal 20 UU PDP)
Pemrosesan Data Pribadi dilakukan berdasarkan: (a) persetujuan eksplisit Subjek Data; (b) pemenuhan kontrak; (c) kewajiban hukum; (d) kepentingan vital Subjek Data; (e) kepentingan umum.

2. HAK SUBJEK DATA PRIBADI (Pasal 5-13 UU PDP)
Subjek Data berhak: (a) mengakses; (b) memperbaiki; (c) menghapus; (d) membatasi pemrosesan; (e) keberatan; (f) portabilitas data; (g) ganti rugi atas pelanggaran; (h) mencabut persetujuan kapan saja.

3. KEAMANAN DATA (Pasal 35 & 39 UU PDP)
Kami menerapkan enkripsi AES-256 at-rest dan TLS 1.3 in-transit, kontrol akses berbasis peran, audit log, dan pengujian penetrasi berkala.

4. NOTIFIKASI INSIDEN (Pasal 46 UU PDP)
Dalam hal terjadi kegagalan pelindungan Data Pribadi, Kami wajib menyampaikan pemberitahuan tertulis paling lambat 3 x 24 jam kepada Subjek Data dan Lembaga Pelindungan Data Pribadi.

5. RETENSI & PENGHAPUSAN DATA (Pasal 43 & 44 UU PDP)
Data Pribadi disimpan selama masa aktif layanan ditambah 5 tahun. Penghapusan permanen dilakukan apabila tujuan pemrosesan berakhir atau atas permohonan penarikan persetujuan.`,
  },
  minimal: {
    document_name: "Kebijakan_Privasi_Minimal.pdf",
    document_text: `KEBIJAKAN PRIVASI

Kami mengumpulkan data pengguna untuk keperluan layanan. Data Anda aman bersama kami. Hubungi privacy@company.com untuk pertanyaan.`,
  },
};
