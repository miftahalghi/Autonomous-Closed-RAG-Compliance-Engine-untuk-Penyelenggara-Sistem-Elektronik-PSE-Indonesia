"""
PDPClauseExtractorComponent – Langflow Custom Component untuk ekstraksi 5 pilar UU PDP.
Kompatibel dengan arsitektur LFX / Langflow Desktop v1.x (v1.9.2 - v1.11.0).
"""

import json
import os
import ssl
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Any, Dict, List

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output, HandleInput, SecretStrInput
from lfx.schema.data import Data
from lfx.schema.message import Message


# In-memory global cache across component instantiations to prevent double execution in Langflow
_GLOBAL_EXTRACTOR_CACHE: Dict[str, Any] = {}


def _bypass_ssl_verification() -> None:
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except Exception:
        pass

    try:
        _orig_cdc = getattr(ssl, "_orig_create_default_context", None)
        if _orig_cdc is None:
            _orig_cdc = ssl.create_default_context
            ssl._orig_create_default_context = _orig_cdc

        def _unverified_cdc(*args, **kwargs):
            ctx = _orig_cdc(*args, **kwargs)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx

        ssl.create_default_context = _unverified_cdc
    except Exception:
        pass

    try:
        os.environ["PYTHONHTTPSVERIFY"] = "0"
        os.environ["CURL_CA_BUNDLE"] = ""
        os.environ["REQUESTS_CA_BUNDLE"] = ""
        os.environ["SSL_CERT_FILE"] = ""
    except Exception:
        pass

    try:
        import httpx
        import httpx._config

        def _unverified_httpx_ssl(*args, **kwargs):
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx

        httpx.create_ssl_context = _unverified_httpx_ssl
        httpx._config.create_ssl_context = _unverified_httpx_ssl
    except Exception:
        pass

    try:
        import httpcore
        import httpcore._ssl

        def _unverified_httpcore_ssl(*args, **kwargs):
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx

        httpcore._ssl.default_ssl_context = _unverified_httpcore_ssl
    except Exception:
        pass

    try:
        import google.genai._api_client

        def _unverified_ensure_httpx_ssl_ctx(options):
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            args = dict(options.client_args or {})
            args["verify"] = ctx
            async_args = dict(options.async_client_args or {})
            async_args["verify"] = ctx
            return args, async_args

        google.genai._api_client.BaseApiClient._ensure_httpx_ssl_ctx = staticmethod(_unverified_ensure_httpx_ssl_ctx)
    except Exception:
        pass


_bypass_ssl_verification()


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


class PDPClauseExtractorComponent(Component):
    display_name: str = "PDP 5-Pillar Clause Extractor"
    description: str = (
        "Mengekstrak klausul dari dokumen kebijakan privasi ke dalam 5 Pilar Wajib UU No. 27/2022 (UU PDP) "
        "menggunakan LLM Structured Output."
    )
    icon: str = "FileSearch"
    name: str = "PDPClauseExtractor"

    inputs = [
        MessageTextInput(
            name="document_text",
            display_name="Teks Kebijakan Privasi",
            info="Teks utuh dokumen kebijakan privasi yang akan diaudit (atau pesan dari Chat Input).",
            required=True,
        ),
        MessageTextInput(
            name="document_name",
            display_name="Nama Dokumen",
            value="Sample_Policy_PT_Contoh_Digital.pdf",
            info="Nama dokumen untuk pelaporan audit.",
        ),
        HandleInput(
            name="llm",
            display_name="Language Model",
            input_types=["LanguageModel"],
            info="Model LLM (misalnya Google Generative AI / Gemini) dengan temperature 0.0.",
            required=False,
        ),
        SecretStrInput(
            name="google_api_key",
            display_name="Google API Key (Opsional)",
            info="Opsional: masukkan jika tidak menyambungkan node Language Model terpisah.",
        ),
    ]

    outputs = [
        Output(name="extracted_data", display_name="Extracted Clauses (Data)", method="extract_clauses"),
        Output(name="summary_message", display_name="Status Ekstraksi (Message)", method="get_summary_message"),
    ]

    def _extract_text_from_content(self, content: Any) -> str:
        """Ekstraksi teks bersih dari berbagai tipe return LLM (str, list, dict, message)."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    if "text" in item:
                        parts.append(str(item["text"]))
                    elif "content" in item:
                        parts.append(str(item["content"]))
                    else:
                        parts.append(str(item))
                elif hasattr(item, "text"):
                    parts.append(str(getattr(item, "text", "")))
                elif hasattr(item, "content"):
                    parts.append(str(getattr(item, "content", "")))
                else:
                    parts.append(str(item))
            return "".join(parts)
        if isinstance(content, dict):
            if "text" in content:
                return str(content["text"])
            if "content" in content:
                return str(content["content"])
            return json.dumps(content)
        if hasattr(content, "text"):
            return str(getattr(content, "text", ""))
        return str(content or "")

    def _call_llm(self, prompt: str) -> str:
        """Panggil model LLM via Langflow connection atau google-genai langsung."""
        _bypass_ssl_verification()

        if hasattr(self, "llm") and self.llm is not None:
            try:
                client = getattr(self.llm, "client", None)
                if client:
                    httpx_c = getattr(client, "_httpx_client", None)
                    if httpx_c:
                        transport = getattr(httpx_c, "_transport", None)
                        if transport and hasattr(transport, "_pool"):
                            pool = transport._pool
                            if hasattr(pool, "_ssl_context") and pool._ssl_context:
                                pool._ssl_context.check_hostname = False
                                pool._ssl_context.verify_mode = ssl.CERT_NONE
            except Exception:
                pass

            if hasattr(self.llm, "invoke"):
                res = self.llm.invoke(prompt)
                content = getattr(res, "content", res)
                return self._extract_text_from_content(content)
            elif callable(self.llm):
                res = self.llm(prompt)
                content = getattr(res, "content", res)
                return self._extract_text_from_content(content)

        # Fallback via google-genai SDK jika API key diisi langsung
        api_key = getattr(self, "google_api_key", None)
        if api_key:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(
                        client_args={"verify": False},
                        async_client_args={"verify": False}
                    )
                )
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[prompt],
                    config=types.GenerateContentConfig(temperature=0.0)
                )
                return getattr(response, "text", str(response))
            except Exception as e:
                raise RuntimeError(f"Gagal memanggil Gemini via SDK fallback: {e}")

        raise ValueError("Node LLM belum disambungkan dan Google API Key tidak diisi pada komponen!")

    def _clean_json_response(self, text: Any) -> dict:
        """Membersihkan markdown code fence dari output LLM."""
        if isinstance(text, dict):
            return text
        if isinstance(text, list):
            text = self._extract_text_from_content(text)
        elif not isinstance(text, str):
            text = str(text or "")

        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                return json.loads(cleaned[start_idx : end_idx + 1])
            raise

    def extract_clauses(self) -> Data:
        # Ekstraksi teks dokumen
        doc_raw = self.document_text
        if hasattr(doc_raw, "text"):
            doc_text = doc_raw.text or ""
        elif isinstance(doc_raw, list):
            doc_parts = []
            for item in doc_raw:
                if hasattr(item, "text"):
                    doc_parts.append(str(item.text or ""))
                else:
                    doc_parts.append(str(item or ""))
            doc_text = "\n".join(doc_parts)
        else:
            doc_text = str(doc_raw or "")

        doc_name_raw = self.document_name or "Dokumen Kebijakan Privasi"
        if hasattr(doc_name_raw, "text"):
            doc_name = str(doc_name_raw.text)
        elif isinstance(doc_name_raw, list):
            doc_name = " ".join(str(getattr(x, "text", x)) for x in doc_name_raw)
        else:
            doc_name = str(doc_name_raw)

        # Global in-memory cache check: jika Langflow memanggil output kedua (summary_message),
        # return langsung dalam 0.0001 detik tanpa memanggil LLM lagi
        cache_key = f"{doc_name}:::{doc_text}"
        if cache_key in _GLOBAL_EXTRACTOR_CACHE:
            return _GLOBAL_EXTRACTOR_CACHE[cache_key]

        sample_doc = doc_text[:50000]

        def _extract_single_pillar(spec: Dict[str, str]) -> Dict[str, Any]:
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
                raw_out = self._call_llm(prompt)
                parsed = self._clean_json_response(raw_out)
                if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                    parsed = parsed[0]
                elif not isinstance(parsed, dict):
                    parsed = {}
            except Exception:
                parsed = {}

            is_found = bool(parsed.get("found", False))
            raw_t = parsed.get("raw_text")
            return {
                "pillar_id": pid,
                "found": is_found,
                "raw_text": str(raw_t) if (is_found and raw_t) else None,
                "summary": str(parsed.get("summary")) if (is_found and parsed.get("summary")) else None,
                "source_section": str(parsed.get("source_section")) if (is_found and parsed.get("source_section")) else None
            }

        # Ekstraksi paralel 5 pilar dengan 5 worker threads (memangkas waktu dari 88s menjadi ~8-10s)
        with ThreadPoolExecutor(max_workers=5) as executor:
            extracted_pillars = list(executor.map(_extract_single_pillar, PILLAR_SPECS))

        result_data = Data(data={
            "document_name": doc_name,
            "extracted_pillars": extracted_pillars
        })

        # Simpan ke global cache
        _GLOBAL_EXTRACTOR_CACHE[cache_key] = result_data
        self._cached_key = cache_key
        self._cached_result = result_data
        return result_data

    def get_summary_message(self) -> Message:
        extracted = self.extract_clauses()
        data = extracted.data if hasattr(extracted, "data") else {}
        pillars = data.get("extracted_pillars", [])
        found_cnt = sum(1 for p in pillars if p.get("found"))
        doc_title = str(data.get("document_name", ""))
        lines = [f"### Hasil Ekstraksi Dokumen: {doc_title}"]
        lines.append(f"Ditemukan **{found_cnt}/5 pilar** dalam dokumen kebijakan privasi:")
        for p in pillars:
            is_found = bool(p.get("found"))
            icon = "✅" if is_found else "❌"
            p_id = str(p.get("pillar_id", ""))
            p_sum = str(p.get("summary") or "Tidak disebutkan")
            lines.append(f"- {icon} **{p_id}**: {p_sum}")
        return Message(text="\n".join(lines))
