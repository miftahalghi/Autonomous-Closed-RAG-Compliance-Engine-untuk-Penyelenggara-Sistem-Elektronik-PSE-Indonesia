import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Copy, Check, AlertTriangle, CheckCircle, XCircle, HelpCircle, BookOpen, FileText } from 'lucide-react';

const STATUS_CONFIG = {
  COMPLIANT: {
    label: 'COMPLIANT',
    badge: 'bg-[#24a148]/20 text-[#42be65] border-[#24a148]/40',
    icon: CheckCircle,
    iconColor: 'text-[#42be65]',
    border: 'border-[#24a148]/20',
    glow: '',
  },
  PARTIAL: {
    label: 'PARTIAL',
    badge: 'bg-[#f1c21b]/15 text-[#f1c21b] border-[#f1c21b]/30',
    icon: AlertTriangle,
    iconColor: 'text-[#f1c21b]',
    border: 'border-[#f1c21b]/20',
    glow: '',
  },
  NON_COMPLIANT: {
    label: 'NON-COMPLIANT',
    badge: 'bg-[#da1e28]/20 text-[#ff8389] border-[#da1e28]/40',
    icon: XCircle,
    iconColor: 'text-[#ff8389]',
    border: 'border-[#da1e28]/30',
    glow: 'ring-1 ring-[#da1e28]/20',
  },
  MISSING: {
    label: 'MISSING',
    badge: 'bg-slate-700 text-slate-300 border-slate-600',
    icon: HelpCircle,
    iconColor: 'text-slate-400',
    border: 'border-slate-600',
    glow: '',
  },
};

const RISK_CONFIG = {
  LOW: { label: 'LOW', cls: 'bg-[#24a148]/15 text-[#42be65] border-[#24a148]/30' },
  MEDIUM: { label: 'MEDIUM', cls: 'bg-[#f1c21b]/15 text-[#f1c21b] border-[#f1c21b]/30' },
  HIGH: { label: 'HIGH', cls: 'bg-[#ff832b]/15 text-[#ff832b] border-[#ff832b]/30' },
  CRITICAL: { label: 'CRITICAL', cls: 'bg-[#da1e28]/20 text-[#ff8389] border-[#da1e28]/40' },
};

const PILLAR_PASAL = {
  PILAR_1: 'Pasal 20 ayat 1 & 2',
  PILAR_2: 'Pasal 5 s.d. 13',
  PILAR_3: 'Pasal 35 & 39',
  PILAR_4: 'Pasal 46 ayat 1–3 · Mandatory 3×24 Jam',
  PILAR_5: 'Pasal 43 & 44',
};

export default function PillarCard({ pillar, showToast }) {
  const [open, setOpen] = useState(pillar.compliance_status !== 'COMPLIANT');
  const [copied, setCopied] = useState(false);

  const status = STATUS_CONFIG[pillar.compliance_status] || STATUS_CONFIG.MISSING;
  const risk = RISK_CONFIG[pillar.risk_level] || RISK_CONFIG.MEDIUM;
  const StatusIcon = status.icon;

  const copyRevision = () => {
    if (!pillar.suggested_revision) return;
    navigator.clipboard.writeText(pillar.suggested_revision).then(() => {
      setCopied(true);
      showToast('Rekomendasi berhasil disalin ke clipboard!', 'success');
      setTimeout(() => setCopied(false), 2500);
    });
  };

  return (
    <div className={`bg-[#161616] border rounded-xl overflow-hidden transition-all ${status.border} ${status.glow}`}>
      {/* Card Header — always visible */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-slate-800/50 transition-colors"
      >
        <StatusIcon size={18} className={status.iconColor + ' flex-shrink-0'} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-slate-400 text-xs font-mono">{pillar.pillar_id}</span>
            <span className="text-white font-semibold text-sm">{pillar.pillar_name}</span>
            {PILLAR_PASAL[pillar.pillar_id] && (
              <span className="text-slate-500 text-xs">· {PILLAR_PASAL[pillar.pillar_id]}</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={`px-2.5 py-1 text-xs font-bold border rounded-full tracking-wide ${status.badge}`}>
            {status.label}
          </span>
          <span className={`px-2.5 py-1 text-xs font-semibold border rounded-full ${risk.cls}`}>
            {risk.label}
          </span>
          {open ? (
            <ChevronUp size={16} className="text-slate-400" />
          ) : (
            <ChevronDown size={16} className="text-slate-400" />
          )}
        </div>
      </button>

      {/* Expanded body */}
      {open && (
        <div className="px-5 pb-5 border-t border-slate-700/60">
          {/* Two-column clause view */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left: Document clause */}
            <div className="bg-slate-900/60 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <FileText size={13} className="text-[#82cfff]" />
                <span className="text-[#82cfff] text-xs font-semibold uppercase tracking-wider">Klausul Dokumen Asli</span>
              </div>
              {pillar.found_in_document && pillar.extracted_text ? (
                <p className="text-slate-300 text-sm leading-relaxed font-mono text-xs whitespace-pre-wrap">
                  "{pillar.extracted_text}"
                </p>
              ) : (
                <div className="flex items-center gap-2 text-slate-500 text-sm">
                  <HelpCircle size={14} />
                  <span>Klausul tidak ditemukan dalam dokumen.</span>
                </div>
              )}
            </div>

            {/* Right: Legal reference */}
            <div className="bg-slate-900/60 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <BookOpen size={13} className="text-[#42be65]" />
                <span className="text-[#42be65] text-xs font-semibold uppercase tracking-wider">Pasal Rujukan Resmi</span>
              </div>
              <div className="space-y-1.5">
                {(pillar.cited_articles || []).map((art, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#42be65] flex-shrink-0" />
                    <span className="text-slate-300 text-xs font-medium">{art}</span>
                  </div>
                ))}
                {(!pillar.cited_articles || pillar.cited_articles.length === 0) && (
                  <span className="text-slate-500 text-xs">Tidak ada pasal yang dikutip.</span>
                )}
              </div>
            </div>
          </div>

          {/* Gap Analysis */}
          <div className="mt-4 bg-slate-900/40 border border-slate-700/60 rounded-lg p-4">
            <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">Analisis Kesenjangan</p>
            <p className={`text-sm leading-relaxed ${
              pillar.compliance_status === 'NON_COMPLIANT' ? 'text-[#ff8389]' :
              pillar.compliance_status === 'PARTIAL' ? 'text-[#f1c21b]' : 'text-slate-300'
            }`}>
              {pillar.analysis}
            </p>
          </div>

          {/* Revision Recommendation */}
          {pillar.suggested_revision && (
            <div className="mt-4 bg-[#0f62fe]/5 border border-[#0f62fe]/30 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <p className="text-[#78a9ff] text-xs font-semibold uppercase tracking-wider">
                  Rekomendasi Revisi Klausul (Ready-to-use)
                </p>
                <button
                  onClick={copyRevision}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all
                    ${copied
                      ? 'bg-[#24a148]/20 text-[#42be65] border border-[#24a148]/40'
                      : 'bg-[#0f62fe]/20 text-[#78a9ff] border border-[#0f62fe]/40 hover:bg-[#0f62fe]/30'}`}
                >
                  {copied ? <Check size={12} /> : <Copy size={12} />}
                  {copied ? 'Tersalin!' : 'Salin Rekomendasi'}
                </button>
              </div>
              <p className="text-slate-200 text-sm leading-relaxed font-mono text-xs whitespace-pre-wrap bg-slate-900/60 rounded-md p-3 border border-slate-700">
                {pillar.suggested_revision}
              </p>
            </div>
          )}

          {/* Compliant — no revision needed */}
          {!pillar.suggested_revision && pillar.compliance_status === 'COMPLIANT' && (
            <div className="mt-4 flex items-center gap-2 text-[#42be65] text-sm bg-[#24a148]/10 border border-[#24a148]/20 rounded-lg px-4 py-3">
              <CheckCircle size={14} />
              <span>Klausul telah memenuhi ketentuan hukum yang berlaku. Tidak diperlukan revisi.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
