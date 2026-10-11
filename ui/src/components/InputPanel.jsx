import React from 'react';
import { FileText, Play, Zap, AlertTriangle } from 'lucide-react';

export default function InputPanel({
  documentName, setDocumentName,
  documentText, setDocumentText,
  onAudit, mode, apiKey,
}) {
  const liveWithoutKey = mode === 'live' && !apiKey?.trim();

  return (
    <div className="mt-8 space-y-5">
      {/* Mode badge */}
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border
        ${mode === 'demo'
          ? 'bg-[#1192e8]/15 text-[#82cfff] border-[#1192e8]/30'
          : 'bg-[#24a148]/15 text-[#42be65] border-[#24a148]/30'}`}
      >
        {mode === 'demo' ? <Zap size={12} /> : <span className="w-1.5 h-1.5 rounded-full bg-[#42be65] animate-pulse" />}
        {mode === 'demo' ? 'Mode: Offline Demo — hasil instan dari dataset pre-baked' : 'Mode: Live Endpoint (Langflow) — koneksi ke Langflow Desktop'}
      </div>

      {/* Warning: live mode but no API key */}
      {liveWithoutKey && (
        <div className="flex items-start gap-3 bg-[#f1c21b]/10 border border-[#f1c21b]/30 rounded-lg px-4 py-3">
          <AlertTriangle size={15} className="text-[#f1c21b] flex-shrink-0 mt-0.5" />
          <p className="text-[#f1c21b] text-xs leading-relaxed">
            <strong>API Key belum diisi.</strong> Klik tombol <strong>Settings</strong> di header untuk memasukkan API Key dari Langflow Desktop, lalu klik <strong>Test Koneksi</strong> untuk verifikasi.
          </p>
        </div>
      )}

      {/* Document name */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1.5">
          Nama Dokumen
        </label>
        <div className="flex items-center gap-2 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 focus-within:border-[#0f62fe] transition-colors">
          <FileText size={15} className="text-slate-400 flex-shrink-0" />
          <input
            type="text"
            value={documentName}
            onChange={(e) => setDocumentName(e.target.value)}
            className="flex-1 bg-transparent text-slate-100 text-sm outline-none placeholder:text-slate-500"
            placeholder="Nama file kebijakan privasi..."
          />
        </div>
      </div>

      {/* Document text */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1.5">
          Teks Kebijakan Privasi
          <span className="ml-2 text-xs text-slate-500 font-normal">
            ({documentText.length.toLocaleString()} karakter)
          </span>
        </label>
        <textarea
          value={documentText}
          onChange={(e) => setDocumentText(e.target.value)}
          rows={14}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-slate-100 text-sm leading-relaxed
            outline-none focus:border-[#0f62fe] transition-colors resize-y placeholder:text-slate-500
            font-mono"
          placeholder={`Tempel teks kebijakan privasi perusahaan di sini...\n\nContoh:\nKAMI MEMPROSES DATA PRIBADI ANDA BERDASARKAN:\na. Persetujuan eksplisit...\nb. Pemenuhan kewajiban kontraktual...`}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={onAudit}
          disabled={!documentText.trim()}
          className="flex items-center gap-2 px-6 py-3 bg-[#0f62fe] hover:bg-[#0353e9] disabled:opacity-40
            disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors shadow-lg shadow-[#0f62fe]/20
            active:scale-95"
        >
          <Play size={16} fill="white" />
          Mulai Audit Kepatuhan UU PDP
        </button>
        {documentText.trim() && (
          <button
            onClick={() => { setDocumentText(''); setDocumentName('Kebijakan_Privasi_PT_Contoh_Digital.pdf'); }}
            className="px-4 py-3 text-sm text-slate-400 hover:text-white border border-slate-600 hover:border-slate-400 rounded-lg transition-colors"
          >
            Bersihkan
          </button>
        )}
      </div>
    </div>
  );
}
