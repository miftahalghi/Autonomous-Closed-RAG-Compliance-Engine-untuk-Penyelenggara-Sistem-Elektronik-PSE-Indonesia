import React, { useState } from 'react';
import ComplianceGauge from './ComplianceGauge';
import PillarCard from './PillarCard';
import AIFooter from './AIFooter';
import { Download, FileJson, Printer, RotateCcw } from 'lucide-react';

const RISK_STYLE = {
  RENDAH: 'bg-[#24a148]/20 text-[#42be65] border-[#24a148]/40',
  SEDANG: 'bg-[#f1c21b]/15 text-[#f1c21b] border-[#f1c21b]/30',
  TINGGI: 'bg-[#ff832b]/15 text-[#ff832b] border-[#ff832b]/30',
  KRITIS: 'bg-[#da1e28]/20 text-[#ff8389] border-[#da1e28]/40',
};

const FILTER_TABS = ['Semua', 'Perlu Perhatian', 'Patuh'];

function pillarsForFilter(pillars, tab) {
  if (tab === 'Semua') return pillars;
  if (tab === 'Patuh') return pillars.filter((p) => p.compliance_status === 'COMPLIANT');
  return pillars.filter((p) => ['PARTIAL', 'NON_COMPLIANT', 'MISSING'].includes(p.compliance_status));
}

export default function ResultsDashboard({ result, showToast, onReset }) {
  const [activeFilter, setActiveFilter] = useState('Semua');

  const pillars = result.pillar_results || [];
  const compliantCount = pillars.filter((p) => p.compliance_status === 'COMPLIANT').length;
  const partialCount = pillars.filter((p) => p.compliance_status === 'PARTIAL').length;
  const nonCompliantCount = pillars.filter((p) => p.compliance_status === 'NON_COMPLIANT').length;
  const missingCount = pillars.filter((p) => p.compliance_status === 'MISSING').length;
  const filtered = pillarsForFilter(pillars, activeFilter);

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_${result.document_name?.replace(/\s+/g, '_')}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Laporan JSON berhasil diunduh.', 'success');
  };

  const exportPrint = () => window.print();

  return (
    <div className="mt-8 space-y-6 print:mt-0">
      {/* Action bar */}
      <div className="flex items-center justify-between flex-wrap gap-3 print:hidden">
        <div>
          <h2 className="text-white font-bold text-xl">Hasil Audit Kepatuhan</h2>
          <p className="text-slate-400 text-sm mt-0.5">{result.document_name}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={exportJSON}
            className="flex items-center gap-2 px-4 py-2 text-sm text-slate-300 hover:text-white border border-slate-600 hover:border-slate-400 rounded-lg transition-colors"
          >
            <FileJson size={14} />
            Export JSON
          </button>
          <button
            onClick={exportPrint}
            className="flex items-center gap-2 px-4 py-2 text-sm text-slate-300 hover:text-white border border-slate-600 hover:border-slate-400 rounded-lg transition-colors"
          >
            <Printer size={14} />
            Cetak / PDF
          </button>
          <button
            onClick={onReset}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-[#0f62fe] hover:bg-[#0353e9] text-white rounded-lg transition-colors"
          >
            <RotateCcw size={14} />
            Audit Baru
          </button>
        </div>
      </div>

      {/* ── Executive Summary Cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Score */}
        <div className="bg-[#161616] border border-slate-700 rounded-xl p-5 flex flex-col items-center">
          <ComplianceGauge score={result.compliance_score} />
          <p className="text-slate-400 text-xs mt-2 text-center">Skor Kepatuhan Keseluruhan</p>
        </div>

        {/* Risk + Summary pills */}
        <div className="md:col-span-2 bg-[#161616] border border-slate-700 rounded-xl p-5 flex flex-col gap-4">
          <div className="flex items-start gap-4 flex-wrap">
            <div>
              <p className="text-slate-500 text-xs font-medium uppercase tracking-wide mb-2">Tingkat Risiko</p>
              <span className={`inline-flex items-center px-4 py-1.5 rounded-full text-sm font-bold border tracking-wider
                ${RISK_STYLE[result.overall_risk] || RISK_STYLE['KRITIS']}`}>
                {result.overall_risk}
              </span>
            </div>
            <div>
              <p className="text-slate-500 text-xs font-medium uppercase tracking-wide mb-2">Ringkasan Pilar</p>
              <div className="flex flex-wrap gap-2">
                {compliantCount > 0 && (
                  <span className="px-2.5 py-1 text-xs font-medium bg-[#24a148]/20 text-[#42be65] border border-[#24a148]/30 rounded-full">
                    {compliantCount} Patuh
                  </span>
                )}
                {partialCount > 0 && (
                  <span className="px-2.5 py-1 text-xs font-medium bg-[#f1c21b]/15 text-[#f1c21b] border border-[#f1c21b]/30 rounded-full">
                    {partialCount} Parsial
                  </span>
                )}
                {nonCompliantCount > 0 && (
                  <span className="px-2.5 py-1 text-xs font-medium bg-[#da1e28]/20 text-[#ff8389] border border-[#da1e28]/40 rounded-full">
                    {nonCompliantCount} Tidak Patuh
                  </span>
                )}
                {missingCount > 0 && (
                  <span className="px-2.5 py-1 text-xs font-medium bg-slate-700 text-slate-300 border border-slate-600 rounded-full">
                    {missingCount} Tidak Ditemukan
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="border-t border-slate-700 pt-3">
            <p className="text-slate-500 text-xs font-medium uppercase tracking-wide mb-2">Ringkasan Eksekutif</p>
            <p className="text-slate-300 text-sm leading-relaxed">{result.summary}</p>
          </div>
        </div>
      </div>

      {/* ── Pillar Cards ── */}
      <div>
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h3 className="text-white font-semibold text-base">Analisis 5 Pilar Kepatuhan</h3>
          {/* Filter tabs */}
          <div className="flex items-center gap-1 bg-slate-800 border border-slate-700 rounded-lg p-1 print:hidden">
            {FILTER_TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveFilter(tab)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors
                  ${activeFilter === tab ? 'bg-[#0f62fe] text-white' : 'text-slate-400 hover:text-white'}`}
              >
                {tab}
                {tab === 'Semua' && <span className="ml-1 text-slate-500">({pillars.length})</span>}
                {tab === 'Patuh' && <span className="ml-1 text-slate-500">({compliantCount})</span>}
                {tab === 'Perlu Perhatian' && <span className="ml-1 text-slate-500">({partialCount + nonCompliantCount + missingCount})</span>}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          {filtered.map((pillar) => (
            <PillarCard key={pillar.pillar_id} pillar={pillar} showToast={showToast} />
          ))}
          {filtered.length === 0 && (
            <div className="text-center py-10 text-slate-500 text-sm">
              Tidak ada pilar yang sesuai dengan filter ini.
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <AIFooter onExportJSON={exportJSON} onPrint={exportPrint} />
    </div>
  );
}
