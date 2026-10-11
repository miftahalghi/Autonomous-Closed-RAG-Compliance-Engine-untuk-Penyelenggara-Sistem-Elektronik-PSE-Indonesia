"""
PDPAuditReporterComponent – Langflow Custom Component untuk Kalkulator Skor & Pelaporan Audit.
Kompatibel dengan arsitektur LFX / Langflow Desktop v1.x (v1.9.2 - v1.11.0).

CHANGELOG:
  v3 – tambah output debug_dump untuk menginspeksi raw data masuk dari compliance_checker.
       Digunakan untuk mendiagnosis skor 0/100 karena field name mismatch antar node.
"""

from typing import Dict, Any, List
from datetime import datetime
import json

from lfx.custom.custom_component.component import Component
from lfx.io import Output, HandleInput, MessageTextInput
from lfx.schema.data import Data
from lfx.schema.message import Message


STATUS_WEIGHT = {
    "COMPLIANT": 100,
    "PARTIAL": 50,
    "NON_COMPLIANT": 0,
    "MISSING": 0,
}

STATUS_ICONS = {
    "COMPLIANT": "✅ COMPLIANT",
    "PARTIAL": "⚠️ PARTIAL",
    "NON_COMPLIANT": "❌ NON_COMPLIANT",
    "MISSING": "⭕ MISSING",
}

RISK_ICONS = {
    "LOW": "🟢 LOW",
    "MEDIUM": "🟡 MEDIUM",
    "HIGH": "🟠 HIGH",
    "CRITICAL": "🔴 CRITICAL",
}


def _unwrap_data(obj: Any) -> dict:
    """
    Unwrap berbagai bentuk input Langflow ke dict Python murni.
    Langflow bisa mengirim: Data object, dict, list of Data, string JSON, dll.
    """
    # Data object dengan .data attribute
    if hasattr(obj, "data"):
        inner = obj.data
        if isinstance(inner, dict):
            return inner
        if isinstance(inner, str):
            try:
                return json.loads(inner)
            except Exception:
                return {"_raw_str": inner}
        if inner is None:
            return {}
        return {"_wrapped": inner}

    # Sudah dict
    if isinstance(obj, dict):
        return obj

    # List — ambil item pertama yang valid
    if isinstance(obj, list):
        for item in obj:
            result = _unwrap_data(item)
            if result:
                return result
        return {}

    # String JSON
    if isinstance(obj, str):
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        return {"_raw_str": obj}

    return {}


def _unwrap_str(obj: Any) -> str:
    """Unwrap MessageTextInput / str ke plain string."""
    if hasattr(obj, "text"):
        return str(obj.text or "")
    if isinstance(obj, list):
        return " ".join(str(getattr(x, "text", x)) for x in obj)
    return str(obj or "")


def _extract_evaluations(input_data: dict) -> list:
    """
    Cari list evaluasi dari berbagai kemungkinan key yang dipakai node upstream.
    compliance_checker_node menyimpan di key "evaluations".
    """
    for key in ("evaluations", "results", "pillar_results", "compliance_results", "data"):
        val = input_data.get(key)
        if isinstance(val, list) and val:
            return val
    return []


class PDPAuditReporterComponent(Component):
    display_name: str = "PDP Audit Reporter & Score Calculator"
    description: str = (
        "Menghitung skor kepatuhan matematis, mengklasifikasi risiko total, "
        "dan menghasilkan laporan matriks audit berformat Markdown dan JSON."
    )
    icon: str = "FileCheck2"
    name: str = "PDPAuditReporter"

    inputs = [
        HandleInput(
            name="compliance_data",
            display_name="Compliance Results Data",
            input_types=["Data"],
            info="Data hasil evaluasi kepatuhan dari komponen Compliance Checker.",
            required=True,
        ),
        MessageTextInput(
            name="document_name",
            display_name="Nama Dokumen (Opsional)",
            value="",
            info="Nama dokumen untuk pelaporan.",
        ),
    ]

    outputs = [
        Output(name="report_markdown", display_name="Laporan Audit (Markdown+JSON)", method="generate_markdown_report"),
        Output(name="report_json",     display_name="Laporan Audit (JSON Data)",      method="generate_json_report"),
        Output(name="debug_dump",      display_name="🔍 DEBUG — Raw Input Dump",      method="generate_debug_dump"),
    ]

    # ------------------------------------------------------------------
    # Core: unwrap + hitung metrik
    # ------------------------------------------------------------------

    def _calculate_metrics(self) -> Dict[str, Any]:
        # 1. Unwrap input dari compliance_checker
        input_data = _unwrap_data(self.compliance_data)

        # 2. Ambil list evaluasi
        evaluations = _extract_evaluations(input_data)

        # 3. Unwrap document_name
        doc_name = _unwrap_str(self.document_name).strip() \
            or input_data.get("document_name", "Dokumen Kebijakan Privasi")

        # 4. Hitung skor
        total_weight = 0
        pilar4_status = None

        for e in evaluations:
            # Key "status" dipakai compliance_checker_node
            raw_status = str(e.get("status") or "MISSING").strip().upper()
            if raw_status not in STATUS_WEIGHT:
                raw_status = "MISSING"
            total_weight += STATUS_WEIGHT[raw_status]
            if str(e.get("pillar_id", "")).upper() == "PILAR_4":
                pilar4_status = raw_status

        score = round((total_weight / 500) * 100, 2)  # denominator selalu 500 (5 × 100)

        # 5. Klasifikasi risiko (sesuai dengan badge di UI)
        if pilar4_status in ("NON_COMPLIANT", "MISSING") or pilar4_status is None:
            overall_risk, risk_badge = "KRITIS", "🔴 KRITIS"
        elif score < 60:
            overall_risk, risk_badge = "TINGGI", "🟠 TINGGI"
        elif score < 85:
            overall_risk, risk_badge = "SEDANG", "🟡 SEDANG"
        else:
            overall_risk, risk_badge = "RENDAH", "🟢 RENDAH"

        # Jika tidak ada pilar4 tapi ada evaluations, override ke TINGGI/SEDANG/RENDAH
        if evaluations and pilar4_status is None:
            if score < 60:
                overall_risk, risk_badge = "TINGGI", "🟠 TINGGI"
            elif score < 85:
                overall_risk, risk_badge = "SEDANG", "🟡 SEDANG"
            else:
                overall_risk, risk_badge = "RENDAH", "🟢 RENDAH"

        return {
            "document_name": doc_name,
            "compliance_score": score,
            "overall_risk": overall_risk,
            "risk_badge": risk_badge,
            "evaluations": evaluations,
            "_input_data_keys": list(input_data.keys()),      # untuk debug
            "_eval_count": len(evaluations),                   # untuk debug
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ------------------------------------------------------------------
    # Output 1: Markdown + JSON block (dibaca UI)
    # ------------------------------------------------------------------

    def generate_markdown_report(self) -> Message:
        metrics = self._calculate_metrics()
        evals   = metrics["evaluations"]
        doc_name     = str(metrics["document_name"])
        score        = str(metrics["compliance_score"])
        risk_badge   = str(metrics["risk_badge"])
        overall_risk = str(metrics["overall_risk"])
        timestamp    = str(metrics["timestamp"])
        eval_count   = metrics["_eval_count"]

        lines = [
            "# 📋 LAPORAN AUDIT KEPATUHAN KEBIJAKAN PRIVASI",
            "**Berdasarkan UU No. 27 Tahun 2022 (UU PDP) · Closed-RAG Deterministic Engine**",
            "",
            f"- **Nama Dokumen**: `{doc_name}`",
            f"- **Skor Kepatuhan**: **`{score}%`**",
            f"- **Klasifikasi Risiko**: **{risk_badge}**",
            f"- **Pilar Dievaluasi**: {eval_count}/5",
            f"- **Waktu Audit**: `{timestamp}`",
            "",
            "---",
            "### 📊 MATRIKS KEPATUHAN 5 PILAR WAJIB",
            "",
            "| ID Pilar | Nama Pilar | Status Kepatuhan | Tingkat Risiko | Dasar Hukum |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for e in evals:
            pid   = str(e.get("pillar_id", ""))
            pname = str(e.get("pillar_name", ""))
            st    = str(e.get("status") or "MISSING").strip().upper()
            rl    = str(e.get("risk_level") or "MEDIUM").strip().upper()
            cited = ", ".join(e.get("cited_articles") or []) or "-"
            lines.append(f"| **{pid}** | {pname} | {STATUS_ICONS.get(st, st)} | {RISK_ICONS.get(rl, rl)} | {cited} |")

        lines += ["", "---", "### 🔍 TEMUAN AUDIT & REKOMENDASI KLAUSUL PERBAIKAN", ""]

        for e in evals:
            pid   = str(e.get("pillar_id", ""))
            pname = str(e.get("pillar_name", ""))
            st    = str(e.get("status") or "MISSING").strip().upper()
            rl    = str(e.get("risk_level") or "MEDIUM").strip().upper()
            gap   = str(e.get("analysis", ""))
            rev   = str(e.get("suggested_revision") or "").strip()
            cited = ", ".join(e.get("cited_articles") or [])

            lines.append(f"#### [{pid}] {pname}")
            lines.append(f"- **Status**: {STATUS_ICONS.get(st, st)} | **Risiko**: {RISK_ICONS.get(rl, rl)}")
            lines.append(f"- **Analisis Gap**: {gap}")
            if cited:
                lines.append(f"- **Pasal Rujukan**: {cited}")
            if rev:
                lines.append("- **Rekomendasi Revisi Klausul (Ready to Copy)**:")
                lines.append(f"  > *{rev}*")
            lines.append("")

        exec_summary = (
            f"Dokumen '{doc_name}' memperoleh skor kepatuhan {score}% ({overall_risk}). "
            "Penyelarasan klausul wajib dilakukan terutama pada pilar yang berstatus PARTIAL atau NON_COMPLIANT "
            "guna menghindari sanksi administratif Pasal 57 UU No. 27/2022."
        )
        lines += ["---", "### 📌 RINGKASAN EKSEKUTIF", exec_summary, ""]

        # ── JSON block — dibaca oleh UI (App.jsx: regex /```json...```/) ──────
        pillar_results = []
        for e in evals:
            raw_status = str(e.get("status") or "MISSING").strip().upper()
            if raw_status not in ("COMPLIANT", "PARTIAL", "NON_COMPLIANT", "MISSING"):
                raw_status = "MISSING"
            raw_risk = str(e.get("risk_level") or "MEDIUM").strip().upper()
            if raw_risk not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
                raw_risk = "MEDIUM"

            pillar_results.append({
                "pillar_id":         str(e.get("pillar_id", "")),
                "pillar_name":       str(e.get("pillar_name", "")),
                # compliance_checker_node menulis "found_in_doc" (bukan "found_in_document")
                "found_in_document": bool(e.get("found_in_doc", e.get("found_in_document", True))),
                "extracted_text":    e.get("extracted_text") or None,
                # compliance_checker_node menulis key "status", UI mengharapkan "compliance_status"
                "compliance_status": raw_status,
                "risk_level":        raw_risk,
                "analysis":          str(e.get("analysis", "")),
                "cited_articles":    list(e.get("cited_articles") or []),
                "suggested_revision": e.get("suggested_revision") or None,
            })

        json_report = {
            "document_name":    doc_name,
            "compliance_score": float(metrics["compliance_score"]),
            "overall_risk":     overall_risk,
            "summary":          exec_summary,
            "pillar_results":   pillar_results,
        }

        lines += [
            "```json",
            json.dumps(json_report, ensure_ascii=False, indent=2),
            "```",
        ]

        return Message(text="\n".join(lines))

    # ------------------------------------------------------------------
    # Output 2: JSON Data
    # ------------------------------------------------------------------

    def generate_json_report(self) -> Data:
        metrics = self._calculate_metrics()
        return Data(data=metrics)

    # ------------------------------------------------------------------
    # Output 3: DEBUG DUMP — hubungkan ke ChatOutput untuk inspect
    # ------------------------------------------------------------------

    def generate_debug_dump(self) -> Message:
        """
        Sambungkan output ini ke ChatOutput sementara untuk debug.
        Akan menampilkan:
          - Semua keys dalam input_data dari compliance_checker
          - Jumlah evaluasi yang diterima
          - Raw JSON dari evaluasi pertama (jika ada)
        Setelah debug selesai, sambungkan kembali ke report_markdown.
        """
        input_data = _unwrap_data(self.compliance_data)
        evaluations = _extract_evaluations(input_data)

        lines = [
            "## 🔍 DEBUG DUMP — PDPAuditReporter",
            "",
            f"**Keys dalam input_data**: `{list(input_data.keys())}`",
            f"**Jumlah evaluasi diterima**: `{len(evaluations)}`",
            "",
        ]

        if evaluations:
            lines.append("**Contoh evaluasi pertama (raw):**")
            lines.append("```json")
            lines.append(json.dumps(evaluations[0], ensure_ascii=False, indent=2, default=str))
            lines.append("```")
            lines.append("")
            lines.append("**Semua pillar_id + status yang diterima:**")
            for e in evaluations:
                pid = e.get("pillar_id", "?")
                st  = e.get("status", "⚠️ KEY 'status' TIDAK ADA — keys: " + str(list(e.keys())))
                lines.append(f"- `{pid}`: `{st}`")
        else:
            lines.append("⚠️ **evaluations KOSONG!**")
            lines.append("")
            lines.append("**Seluruh isi input_data (raw):**")
            lines.append("```json")
            lines.append(json.dumps(input_data, ensure_ascii=False, indent=2, default=str)[:3000])
            lines.append("```")

        return Message(text="\n".join(lines))
