"""
PDPLegalRetrieverComponent – Langflow Custom Component untuk Closed-RAG Retrieval UU PDP.
Kompatibel dengan arsitektur LFX / Langflow Desktop v1.x (v1.9.2 - v1.11.0).
"""

from typing import Dict, Any, List

from lfx.custom.custom_component.component import Component
from lfx.io import Output, HandleInput
from lfx.schema.data import Data
from lfx.schema.message import Message

# Ground Truth Naskah Resmi UU No. 27 Tahun 2022 (LNRI Tahun 2022 No. 196)
OFFICIAL_UU_PDP_ARTICLES: Dict[str, Dict[str, Any]] = {
    "PILAR_1": {
        "name": "Dasar Pemrosesan Data",
        "pasal_list": ["Pasal 20"],
        "content": (
            "Pasal 20 UU No. 27 Tahun 2022:\n"
            "(1) Pengendali Data Pribadi wajib memiliki dasar pemrosesan Data Pribadi.\n"
            "(2) Dasar pemrosesan Data Pribadi sebagaimana dimaksud pada ayat (1) meliputi:\n"
            "a. persetujuan yang sah secara eksplisit dari Subjek Data Pribadi untuk 1 (satu) atau beberapa tujuan tertentu yang telah disampaikan oleh Pengendali Data Pribadi kepada Subjek Data Pribadi;\n"
            "b. pemenuhan kewajiban perjanjian dalam hal Subjek Data Pribadi merupakan salah satu pihak atau untuk memenuhi permintaan Subjek Data Pribadi pada saat akan melakukan perjanjian;\n"
            "c. pemenuhan kewajiban hukum dari Pengendali Data Pribadi sesuai dengan ketentuan peraturan perundang-undangan;\n"
            "d. pemenuhan pelindungan kepentingan vital Subjek Data Pribadi;\n"
            "e. pelaksanaan tugas dalam rangka kepentingan umum, pelayanan publik, atau pelaksanaan kewenangan Pengendali Data Pribadi berdasarkan peraturan perundang-undangan; dan/atau\n"
            "f. pemenuhan kepentingan yang sah lainnya dengan memperhatikan tujuan, kebutuhan, dan keseimbangan kepentingan Pengendali Data Pribadi dan hak Subjek Data Pribadi."
        )
    },
    "PILAR_2": {
        "name": "Hak Subjek Data Pribadi",
        "pasal_list": ["Pasal 5", "Pasal 6", "Pasal 7", "Pasal 8", "Pasal 9", "Pasal 10", "Pasal 11", "Pasal 12", "Pasal 13"],
        "content": (
            "Pasal 5 s.d. Pasal 13 UU No. 27 Tahun 2022:\n"
            "Pasal 5: Subjek Data Pribadi berhak mendapatkan informasi tentang kejelasan identitas, dasar kepentingan hukum, tujuan permintaan dan penggunaan Data Pribadi, dan akuntabilitas pihak yang meminta Data Pribadi.\n"
            "Pasal 6: Subjek Data Pribadi berhak melengkapi, memperbarui, dan/atau memperbaiki kesalahan dan/atau ketidakakuratan Data Pribadi tentang dirinya sesuai dengan tujuan pemrosesan Data Pribadi.\n"
            "Pasal 7: Subjek Data Pribadi berhak mendapatkan akses dan memperoleh salinan Data Pribadi tentang dirinya sesuai dengan ketentuan peraturan perundang-undangan.\n"
            "Pasal 8: Subjek Data Pribadi berhak untuk mengakhiri pemrosesan, menghapus, dan/atau memusnahkan Data Pribadi tentang dirinya sesuai dengan ketentuan peraturan perundang-undangan.\n"
            "Pasal 9: Subjek Data Pribadi berhak menarik kembali persetujuan pemrosesan Data Pribadi tentang dirinya yang telah diberikan kepada Pengendali Data Pribadi.\n"
            "Pasal 10: Subjek Data Pribadi berhak untuk mengajukan keberatan atas tindakan pengambilan keputusan yang hanya didasarkan pada pemrosesan secara otomatis, termasuk pemrofilan, yang menimbulkan akibat hukum atau berdampak signifikan pada Subjek Data Pribadi.\n"
            "Pasal 11: Subjek Data Pribadi berhak menunda atau membatasi pemrosesan Data Pribadi secara proporsional sesuai dengan tujuan pemrosesan Data Pribadi.\n"
            "Pasal 12: Subjek Data Pribadi berhak menggugat dan menerima ganti rugi atas pelanggaran pemrosesan Data Pribadi tentang dirinya.\n"
            "Pasal 13: Subjek Data Pribadi berhak mendapatkan dan/atau menggunakan Data Pribadi tentang dirinya dari Pengendali Data Pribadi dalam bentuk yang lazim digunakan atau dapat dibaca oleh sistem elektronik (hak portabilitas data)."
        )
    },
    "PILAR_3": {
        "name": "Kewajiban Pengamanan & Pengendalian",
        "pasal_list": ["Pasal 35", "Pasal 39"],
        "content": (
            "Pasal 35 UU No. 27 Tahun 2022:\n"
            "(1) Pengendali Data Pribadi wajib melindungi dan memastikan keamanan Data Pribadi yang diprosesnya, dengan melakukan:\n"
            "a. penyusunan dan penerapan langkah teknis operasional untuk melindungi Data Pribadi dari gangguan pemrosesan Data Pribadi yang bertentangan dengan ketentuan peraturan perundang-undangan; dan\n"
            "b. penentuan tingkat keamanan Data Pribadi dengan memperhatikan sifat dan risiko dari Data Pribadi yang harus dilindungi dalam pemrosesan Data Pribadi.\n"
            "(2) Dalam melakukan pemrosesan Data Pribadi, Pengendali Data Pribadi wajib menjaga kerahasiaan Data Pribadi.\n"
            "(3) Kewajiban menjaga kerahasiaan Data Pribadi sebagaimana dimaksud pada ayat (2) berlaku juga terhadap Prosesor Data Pribadi.\n\n"
            "Pasal 39 UU No. 27 Tahun 2022:\n"
            "(1) Pengendali Data Pribadi wajib mencegah Data Pribadi diakses secara tidak sah dengan menerapkan sistem keamanan terhadap Data Pribadi yang diprosesnya.\n"
            "(2) Penerapan sistem keamanan sebagaimana dimaksud pada ayat (1) dilakukan dengan:\n"
            "a. menyusun dan menerapkan langkah teknis dan operasional untuk melindungi Data Pribadi;\n"
            "b. menentukan tingkat keamanan Data Pribadi dengan memperhatikan sifat dan risiko dari Data Pribadi yang harus dilindungi; dan\n"
            "c. memastikan langkah teknis operasional sebagaimana dimaksud pada huruf a dan huruf b dilakukan sesuai dengan standar keamanan yang berlaku."
        )
    },
    "PILAR_4": {
        "name": "Notifikasi Insiden Kebocoran Data",
        "pasal_list": ["Pasal 46"],
        "content": (
            "Pasal 46 UU No. 27 Tahun 2022:\n"
            "(1) Dalam hal terjadi kegagalan Pelindungan Data Pribadi, Pengendali Data Pribadi wajib menyampaikan pemberitahuan secara tertulis paling lambat 3 x 24 (tiga kali dua puluh empat) jam kepada:\n"
            "a. Subjek Data Pribadi; dan\n"
            "b. lembaga.\n"
            "(2) Pemberitahuan tertulis sebagaimana dimaksud pada ayat (1) minimal memuat:\n"
            "a. Data Pribadi yang terungkap;\n"
            "b. kapan dan bagaimana Data Pribadi terungkap; dan\n"
            "c. upaya penanganan dan pemulihan atas terungkapnya Data Pribadi oleh Pengendali Data Pribadi.\n"
            "(3) Dalam hal tertentu, Pengendali Data Pribadi wajib memberitahukan kepada masyarakat mengenai kegagalan Pelindungan Data Pribadi."
        )
    },
    "PILAR_5": {
        "name": "Retensi & Penghapusan Data",
        "pasal_list": ["Pasal 43", "Pasal 44"],
        "content": (
            "Pasal 43 UU No. 27 Tahun 2022:\n"
            "(1) Pengendali Data Pribadi wajib menghapus Data Pribadi dalam hal:\n"
            "a. Data Pribadi telah tidak lagi diperlukan untuk pencapaian tujuan pemrosesan Data Pribadi;\n"
            "b. Subjek Data Pribadi telah melakukan penarikan kembali persetujuan pemrosesan Data Pribadi;\n"
            "c. terdapat permintaan dari Subjek Data Pribadi; atau\n"
            "d. Data Pribadi diperoleh dan/atau diproses dengan cara melawan hukum.\n\n"
            "Pasal 44 UU No. 27 Tahun 2022:\n"
            "(1) Pengendali Data Pribadi wajib memusnahkan Data Pribadi dalam hal:\n"
            "a. masa retensi telah berakhir dan terdapat keterangan untuk dimusnahkan berdasarkan jadwal retensi arsip;\n"
            "b. terdapat permintaan dari Subjek Data Pribadi, kecuali ditentukan lain oleh peraturan perundang-undangan; atau\n"
            "c. tidak berkaitan dengan penyelesaian proses hukum suatu perkara.\n"
            "(2) Pemusnahan Data Pribadi sebagaimana dimaksud pada ayat (1) dilakukan dengan cara:\n"
            "a. tidak menampilkan kembali Data Pribadi dalam sistem elektronik; dan/atau\n"
            "b. merusak fisik dokumen Data Pribadi."
        )
    }
}


class PDPLegalRetrieverComponent(Component):
    display_name: str = "Targeted Legal Retriever (Closed-RAG)"
    description: str = (
        "Mengambil teks resmi pasal UU No. 27/2022 (LNRI 196) yang menjadi dasar hukum mandat "
        "untuk 5 pilar wajib secara tertutup (closed-world)."
    )
    icon: str = "BookMarked"
    name: str = "PDPLegalRetriever"

    inputs = [
        HandleInput(
            name="extracted_data",
            display_name="Extracted Clauses Data",
            input_types=["Data"],
            info="Data hasil ekstraksi klausul dari komponen PDP Clause Extractor.",
            required=True,
        ),
    ]

    outputs = [
        Output(name="retrieved_context", display_name="Retrieved Legal Context (Data)", method="retrieve_context"),
        Output(name="preview_message", display_name="Ringkasan Konteks Hukum (Message)", method="get_preview_message"),
    ]

    def retrieve_context(self) -> Data:
        input_data = self.extracted_data.data if hasattr(self.extracted_data, "data") else {}
        extracted_pillars = input_data.get("extracted_pillars", [])
        doc_name = input_data.get("document_name", "privacy_policy")

        paired_results = []
        for p in extracted_pillars:
            pid = p.get("pillar_id")
            official_ref = OFFICIAL_UU_PDP_ARTICLES.get(pid, {
                "name": pid,
                "pasal_list": [],
                "content": "Tidak ada pasal terdaftar."
            })

            paired_results.append({
                "pillar_id": pid,
                "pillar_name": official_ref["name"],
                "pasal_target": official_ref["pasal_list"],
                "found_in_doc": p.get("found", False),
                "raw_clause_text": p.get("raw_text") if p.get("found") else None,
                "summary": p.get("summary"),
                "source_section": p.get("source_section"),
                "official_articles_text": official_ref["content"]
            })

        return Data(data={
            "document_name": doc_name,
            "paired_pillars": paired_results
        })

    def get_preview_message(self) -> Message:
        res = self.retrieve_context()
        data = res.data if hasattr(res, "data") else {}
        pairs = data.get("paired_pillars", [])
        lines = ["### Konteks Hukum UU No. 27/2022 (Resmi LNRI 196) Berhasil Dipetakan:"]
        for item in pairs:
            pid = str(item.get("pillar_id", ""))
            pname = str(item.get("pillar_name", ""))
            pasal_list = item.get("pasal_target") or []
            pasal_str = ", ".join(pasal_list) if pasal_list else "-"
            is_found = bool(item.get("found_in_doc"))
            found_str = "Klausul Ditemukan" if is_found else "Klausul Nihil"
            lines.append(f"- **{pid} ({pname})**: Rujukan {pasal_str} ({found_str})")
        return Message(text="\n".join(lines))
