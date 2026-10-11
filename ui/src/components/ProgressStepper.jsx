import React from 'react';
import { CheckCircle, Loader, Circle } from 'lucide-react';

const STEPS = [
  { label: 'Ingestion & Structural Document Parsing', sub: 'Memproses struktur dokumen kebijakan privasi...' },
  { label: 'Parallel 5-Pillar Clause Extraction', sub: 'Mengekstrak klausul dari 5 pilar kepatuhan...' },
  { label: 'Metadata-Boosted Retrieval dari Korpus UU PDP (LNRI No. 196)', sub: 'Mengambil pasal-pasal referensi dari basis data hukum...' },
  { label: 'Strict Closed-RAG Compliance Reasoning (Temperature = 0.0)', sub: 'Menjalankan analisis kepatuhan berbasis hukum...' },
  { label: 'Risk Scoring & Executive Report Synthesis', sub: 'Menyusun laporan eksekutif dan skor kepatuhan...' },
];

export default function ProgressStepper({ currentStep, elapsed }) {
  return (
    <div className="mt-12 flex flex-col items-center">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 mb-3">
          <div className="w-2.5 h-2.5 rounded-full bg-[#0f62fe] animate-pulse" />
          <span className="text-[#78a9ff] text-sm font-medium tracking-wide uppercase">Audit Sedang Berjalan</span>
        </div>
        <p className="text-slate-400 text-sm">Mesin Closed-RAG sedang menganalisis dokumen kebijakan privasi...</p>
      </div>

      {/* Steps */}
      <div className="w-full max-w-2xl space-y-0">
        {STEPS.map((step, idx) => {
          const stepNum = idx + 1;
          const isDone = currentStep > stepNum;
          const isActive = currentStep === stepNum;
          const isPending = currentStep < stepNum;

          return (
            <div key={idx} className="flex gap-4">
              {/* Connector */}
              <div className="flex flex-col items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-500
                  ${isDone ? 'bg-[#24a148]' : isActive ? 'bg-[#0f62fe] ring-4 ring-[#0f62fe]/20' : 'bg-slate-700 border border-slate-600'}`}
                >
                  {isDone ? (
                    <CheckCircle size={16} className="text-white" />
                  ) : isActive ? (
                    <Loader size={14} className="text-white animate-spin" />
                  ) : (
                    <span className="text-slate-400 text-xs font-mono">{stepNum}</span>
                  )}
                </div>
                {idx < STEPS.length - 1 && (
                  <div className={`w-0.5 h-8 mt-0.5 transition-all duration-700
                    ${isDone ? 'bg-[#24a148]' : 'bg-slate-700'}`}
                  />
                )}
              </div>

              {/* Content */}
              <div className={`pb-8 pt-1.5 flex-1 transition-opacity duration-300 ${isPending ? 'opacity-40' : 'opacity-100'}`}>
                <p className={`text-sm font-semibold leading-tight
                  ${isDone ? 'text-[#42be65]' : isActive ? 'text-white' : 'text-slate-500'}`}>
                  {isDone ? '✓ ' : ''}{step.label}
                </p>
                {isActive && (
                  <p className="text-xs text-[#82cfff] mt-1 animate-pulse">{step.sub}</p>
                )}
                {isDone && (
                  <p className="text-xs text-slate-500 mt-1">Selesai</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Timer */}
      <div className="mt-4 flex items-center gap-3 text-slate-400 text-sm">
        <div className="w-1.5 h-1.5 rounded-full bg-[#0f62fe] animate-ping" />
        <span>Waktu berjalan: <span className="font-mono text-white">{elapsed}s</span></span>
        <span className="text-slate-600">·</span>
        <span>Estimasi selesai: <span className="font-mono text-slate-300">~10–60 detik</span></span>
      </div>
    </div>
  );
}
