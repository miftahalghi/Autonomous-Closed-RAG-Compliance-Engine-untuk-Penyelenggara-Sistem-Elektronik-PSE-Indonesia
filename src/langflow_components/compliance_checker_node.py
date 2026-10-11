"""
PDPComplianceCheckerComponent – Langflow Custom Component untuk Strict Closed-RAG Compliance Checker.
Kompatibel dengan arsitektur LFX / Langflow Desktop v1.x (v1.9.2 - v1.11.0).
"""

import json
import os
import ssl
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List

from lfx.custom.custom_component.component import Component
from lfx.io import Output, HandleInput, SecretStrInput
from lfx.schema.data import Data
from lfx.schema.message import Message


_GLOBAL_COMPLIANCE_CACHE: Dict[str, Any] = {}


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


class PDPComplianceCheckerComponent(Component):
    display_name: str = "Strict Closed-RAG Compliance Checker"
    description: str = (
        "Mengevaluasi kepatuhan klausul kebijakan privasi terhadap pasal resmi UU PDP "
        "secara tertutup (Strict Grounding, Temperature 0.0) tanpa halusinasi eksternal."
    )
    icon: str = "ShieldCheck"
    name: str = "PDPComplianceChecker"

    inputs = [
        HandleInput(
            name="retrieved_data",
            display_name="Retrieved Legal Context Data",
            input_types=["Data"],
            info="Data pasangan klausul dokumen dan pasal resmi UU PDP dari komponen Legal Retriever.",
            required=True,
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
        Output(name="compliance_results", display_name="Compliance Results (Data)", method="evaluate_compliance"),
        Output(name="status_message", display_name="Status Evaluasi (Message)", method="get_status_message"),
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

        # Fallback via SDK jika API key diisi
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

    def evaluate_compliance(self) -> Data:
        input_data = self.retrieved_data.data if hasattr(self.retrieved_data, "data") else {}
        paired_pillars = input_data.get("paired_pillars", [])
        doc_name = input_data.get("document_name", "privacy_policy")

        # Caching untuk mencegah evaluasi ulang jika dipanggil oleh beberapa output port
        try:
            cache_key = json.dumps(input_data, sort_keys=True)
        except Exception:
            cache_key = str(input_data)

        if cache_key in _GLOBAL_COMPLIANCE_CACHE:
            return _GLOBAL_COMPLIANCE_CACHE[cache_key]

        if getattr(self, "_cached_key", None) == cache_key and getattr(self, "_cached_result", None) is not None:
            return self._cached_result

        instruction_lines = [
            "Anda adalah Auditor Kepatuhan Hukum Tertutup (Closed Legal Auditor) untuk UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi.",
            "",
            "ATURAN STRICT GROUNDING (ANTI-HALUSINASI):",
            "1. Anda HANYA BOLEH menggunakan dasar hukum dari [KONTEKS PASAL RESMI] yang disediakan.",
            "2. DILARANG KERAS mengutip pasal atau ayat yang tidak tertulis di dalam [KONTEKS PASAL RESMI].",
            "3. Klasifikasikan status secara objektif:",
            "   - COMPLIANT: Dokumen memenuhi seluruh syarat dan batas waktu yang diwajibkan pasal secara tegas.",
            "   - PARTIAL: Dokumen menyebutkan topik tersebut namun ada syarat penting/batas waktu yang kurang atau ambigu.",
            "   - NON_COMPLIANT: Dokumen secara langsung melanggar atau menafikan hak/kewajiban dalam pasal.",
            "   - MISSING: Dokumen tidak memiliki klausul sama sekali terkait pilar ini.",
            "4. Tingkat risiko (risk_level): LOW, MEDIUM, HIGH, atau CRITICAL.",
            "5. Tulis rekomendasi klausul perbaikan yang siap disalin oleh tim legal organisasi.",
            "",
            "Kembalikan HANYA format JSON valid:",
            "```json",
            "{",
            '  "pillar_id": "PILAR_...",',
            '  "status": "COMPLIANT | PARTIAL | NON_COMPLIANT | MISSING",',
            '  "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",',
            '  "analysis": "Penjelasan detail gap analysis...",',
            '  "cited_articles": ["Pasal ..."],',
            '  "suggested_revision": "Teks rekomendasi klausul..."',
            "}",
            "```"
        ]
        system_instruction = "\n".join(instruction_lines)

        def _evaluate_single_pillar(item: Dict[str, Any]) -> Dict[str, Any]:
            pid = str(item.get("pillar_id", ""))
            pname = str(item.get("pillar_name", ""))
            found = bool(item.get("found_in_doc"))
            raw_text = str(item.get("raw_clause_text") or "")
            legal_ctx = str(item.get("official_articles_text") or "")

            if found and raw_text:
                clause_box = f"```\n{raw_text}\n```"
            else:
                clause_box = "[KLAUSUL TIDAK DITEMUKAN / NIHIL]"

            legal_box = f"```\n{legal_ctx}\n```"

            prompt_blocks = [
                system_instruction,
                "",
                f"PILAR AUDIT: {pid} - {pname}",
                "",
                "KLAUSUL DOKUMEN ORGANISASI:",
                clause_box,
                "",
                "KONTEKS PASAL RESMI UU PDP (GROUND TRUTH):",
                legal_box,
                "",
                "Kembalikan evaluasi dalam format JSON sesuai spesifikasi di atas."
            ]
            prompt = "\n".join(prompt_blocks)

            try:
                raw_out = self._call_llm(prompt)
                eval_dict = self._clean_json_response(raw_out)
                if isinstance(eval_dict, list) and len(eval_dict) > 0 and isinstance(eval_dict[0], dict):
                    eval_dict = eval_dict[0]
                elif not isinstance(eval_dict, dict):
                    eval_dict = {}
            except Exception as e:
                eval_dict = {
                    "status": "MISSING",
                    "risk_level": "HIGH",
                    "analysis": f"Evaluasi otomatis terkendala: {e}",
                    "cited_articles": [],
                    "suggested_revision": ""
                }

            return {
                "pillar_id": pid,
                "pillar_name": pname,
                "found_in_doc": found,
                "extracted_text": raw_text if found else None,
                "status": eval_dict.get("status", "MISSING"),
                "risk_level": eval_dict.get("risk_level", "HIGH"),
                "analysis": eval_dict.get("analysis", ""),
                "cited_articles": eval_dict.get("cited_articles", []),
                "suggested_revision": eval_dict.get("suggested_revision", "")
            }

        # Evaluasi paralel 5 pilar untuk memangkas latensi dari ~95s ke ~18s
        max_workers = min(5, len(paired_pillars)) if paired_pillars else 1
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            evaluations = list(executor.map(_evaluate_single_pillar, paired_pillars))

        result_data = Data(data={
            "document_name": doc_name,
            "evaluations": evaluations
        })
        _GLOBAL_COMPLIANCE_CACHE[cache_key] = result_data
        self._cached_key = cache_key
        self._cached_result = result_data
        return result_data

    def get_status_message(self) -> Message:
        res = self.evaluate_compliance()
        data = res.data if hasattr(res, "data") else {}
        evals = data.get("evaluations", [])
        lines = ["### Status Evaluasi Kepatuhan Per-Pilar:"]
        for e in evals:
            p_id = str(e.get("pillar_id", ""))
            p_name = str(e.get("pillar_name", ""))
            st = str(e.get("status", ""))
            rl = str(e.get("risk_level", ""))
            lines.append(f"- **{p_id} ({p_name})**: Status `{st}` (Risiko: `{rl}`)")
        return Message(text="\n".join(lines))
