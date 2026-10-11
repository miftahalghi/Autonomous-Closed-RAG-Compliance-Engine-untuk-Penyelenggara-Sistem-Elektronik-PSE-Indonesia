import React from 'react';
import { ShieldCheck, FileJson, Printer } from 'lucide-react';

export default function AIFooter({ onExportJSON, onPrint }) {
  return (
    <div className="mt-8 border-t border-slate-700/60 pt-6 space-y-4">
      {/* Disclaimer */}
      <div className="bg-[#161616] border border-slate-700 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <ShieldCheck size={18} className="text-[#78a9ff] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-[#78a9ff] text-xs font-semibold uppercase tracking-wider mb-2">
              Responsible AI & Transparansi Sistem
            </p>
            <p className="text-slate-400 text-xs leading-relaxed">
              <strong className="text-slate-300">Legal Grounding:</strong> Sistem ini beroperasi dalam mode Closed-RAG penuh. LLM dilarang mengutip regulasi eksternal atau berhalusinasi di luar teks resmi <strong className="text-slate-300">UU No. 27/2022 tentang Pelindungan Data Pribadi (LNRI No. 196)</strong>. Seluruh analisis didasarkan secara eksklusif pada corpus hukum yang telah diverifikasi.
            </p>
            <p className="text-slate-500 text-xs mt-2 leading-relaxed">
              <strong className="text-slate-400">Human-in-the-Loop:</strong> Seluruh rekomendasi yang dihasilkan sistem ini ditujukan untuk mendukung keputusan penasihat hukum resmi dan tidak dapat menggantikan nasihat hukum profesional. Pengguna bertanggung jawab penuh atas implementasi rekomendasi dalam kebijakan perusahaan.
            </p>
            <p className="text-slate-500 text-xs mt-2 leading-relaxed">
              <strong className="text-slate-400">Temperature = 0.0:</strong> Inferensi dijalankan dengan temperature deterministik penuh untuk memastikan konsistensi dan reproducibility hasil audit.
            </p>
          </div>
        </div>
      </div>

      {/* Export actions */}
      <div className="flex items-center justify-between flex-wrap gap-3 print:hidden">
        <p className="text-slate-500 text-xs">
          Audit PDP Engine · Powered by IBM watsonx + Langflow · UU No. 27 Tahun 2022
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={onExportJSON}
            className="flex items-center gap-2 px-4 py-2 text-xs text-slate-300 hover:text-white border border-slate-600 hover:border-slate-400 rounded-lg transition-colors"
          >
            <FileJson size={13} />
            Export Laporan Lengkap (JSON)
          </button>
          <button
            onClick={onPrint}
            className="flex items-center gap-2 px-4 py-2 text-xs text-slate-300 hover:text-white border border-slate-600 hover:border-slate-400 rounded-lg transition-colors"
          >
            <Printer size={13} />
            Cetak / Export PDF
          </button>
        </div>
      </div>
    </div>
  );
}
