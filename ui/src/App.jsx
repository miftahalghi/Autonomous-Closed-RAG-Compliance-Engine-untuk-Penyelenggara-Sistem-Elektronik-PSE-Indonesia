import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import InputPanel from './components/InputPanel';
import ProgressStepper from './components/ProgressStepper';
import ResultsDashboard from './components/ResultsDashboard';
import { MOCK_RESULT, SAMPLE_POLICIES } from './mockData';

// Langflow Desktop v1.11 — port 7860
// Vite proxy strips /langflow prefix → hits http://localhost:7860/api/v1/run/{flowId}
const FLOW_ID = 'a98e2140-5b18-4d56-8e12-pdp272022flow';
const LANGFLOW_URL = `/langflow/api/v1/run/${FLOW_ID}`;

export default function App() {
  const [mode, setMode] = useState('demo'); // 'demo' | 'live'
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('pdp_langflow_apikey') || '');
  const [flowId, setFlowId] = useState(() => localStorage.getItem('pdp_langflow_flowid') || FLOW_ID);
  const [documentName, setDocumentName] = useState('Kebijakan_Privasi_PT_Contoh_Digital.pdf');
  const [documentText, setDocumentText] = useState('');
  const [phase, setPhase] = useState('idle'); // 'idle' | 'running' | 'done' | 'error'
  const [currentStep, setCurrentStep] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);

  // Persist settings to localStorage
  useEffect(() => { localStorage.setItem('pdp_langflow_apikey', apiKey); }, [apiKey]);
  useEffect(() => { localStorage.setItem('pdp_langflow_flowid', flowId); }, [flowId]);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const loadSample = (key) => {
    const s = SAMPLE_POLICIES[key];
    setDocumentName(s.document_name);
    setDocumentText(s.document_text);
    setPhase('idle');
    setResult(null);
    setError(null);
  };

  const startTimer = () => {
    startTimeRef.current = Date.now();
    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 200);
  };

  const stopTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
  };

  useEffect(() => () => stopTimer(), []);

  const runAudit = async () => {
    if (!documentText.trim()) {
      showToast('Masukkan teks kebijakan privasi terlebih dahulu.', 'error');
      return;
    }
    if (mode === 'live' && !apiKey.trim()) {
      showToast('API Key Langflow diperlukan untuk mode Live. Isi di panel Settings.', 'error');
      return;
    }
    setPhase('running');
    setResult(null);
    setError(null);
    setCurrentStep(0);
    setElapsed(0);
    startTimer();

    if (mode === 'demo') {
      // Simulate 5 steps with realistic timing
      const stepDelays = [1800, 1400, 2300, 2700, 1800];
      for (let i = 0; i < 5; i++) {
        await new Promise((r) => setTimeout(r, stepDelays[i]));
        setCurrentStep(i + 1);
      }
      await new Promise((r) => setTimeout(r, 400));
      stopTimer();
      setResult(MOCK_RESULT);
      setPhase('done');
    } else {
      // Live mode — call Langflow Desktop API
      try {
        const endpoint = `/langflow/api/v1/run/${flowId.trim() || FLOW_ID}`;
        const payload = {
          input_value: JSON.stringify({
            document_name: documentName,
            document_text: documentText,
          }),
          input_type: 'text',
          output_type: 'text',
          tweaks: {},
        };

        // Advance stepper while waiting
        let stepIdx = 0;
        const stepTimer = setInterval(() => {
          if (stepIdx < 4) setCurrentStep(++stepIdx);
        }, 8000);

        const headers = { 'Content-Type': 'application/json' };
        if (apiKey.trim()) headers['x-api-key'] = apiKey.trim();

        const res = await fetch(endpoint, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload),
        });

        clearInterval(stepTimer);
        stopTimer();

        if (res.status === 401 || res.status === 403) {
          throw new Error('Autentikasi gagal (401/403). Periksa API Key di Settings.');
        }
        if (!res.ok) {
          const body = await res.text().catch(() => '');
          throw new Error(`Langflow error ${res.status}: ${body || res.statusText}`);
        }

        const data = await res.json();
        // Langflow v1 response shape:
        // data.outputs[0].outputs[0].results.message.text  → string (JSON atau Markdown+JSON)
        const raw = data?.outputs?.[0]?.outputs?.[0]?.results?.message?.text
          ?? data?.outputs?.[0]?.outputs?.[0]?.artifacts?.message
          ?? null;

        if (!raw) throw new Error('Response Langflow tidak mengandung output teks. Periksa konfigurasi ChatOutput node.');

        let parsed;
        try {
          // Coba 1: raw adalah pure JSON
          parsed = JSON.parse(raw);
        } catch {
          // Coba 2: raw adalah Markdown yang mengandung ```json ... ``` block
          const jsonBlockMatch = raw.match(/```json\s*([\s\S]*?)```/);
          if (jsonBlockMatch) {
            try {
              parsed = JSON.parse(jsonBlockMatch[1].trim());
            } catch (e2) {
              throw new Error(`JSON di dalam blok Markdown tidak valid: ${e2.message}`);
            }
          } else {
            // Coba 3: cari objek JSON di mana saja dalam string
            const jsonObjMatch = raw.match(/(\{[\s\S]*"pillar_results"[\s\S]*\})/);
            if (jsonObjMatch) {
              try {
                parsed = JSON.parse(jsonObjMatch[1]);
              } catch {
                throw new Error('Output Langflow bukan JSON valid dan tidak mengandung blok ```json```. Pastikan Reporter node sudah diupdate.');
              }
            } else {
              throw new Error('Output Langflow tidak mengandung JSON. Pastikan reporter_node.py sudah diupdate dan flow di-reload di Langflow Desktop.');
            }
          }
        }

        setCurrentStep(5);
        setResult(parsed);
        setPhase('done');
      } catch (e) {
        stopTimer();
        setError(e.message);
        setPhase('error');
      }
    }
  };

  const reset = () => {
    setPhase('idle');
    setResult(null);
    setError(null);
    setCurrentStep(0);
    setElapsed(0);
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-100 font-sans">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 px-5 py-3 rounded-lg text-sm font-medium shadow-xl
            ${toast.type === 'error' ? 'bg-[#da1e28] text-white' : 'bg-[#24a148] text-white'}`}
        >
          {toast.msg}
        </div>
      )}

      <Header
        mode={mode}
        setMode={setMode}
        loadSample={loadSample}
        onReset={phase !== 'idle' ? reset : undefined}
        apiKey={apiKey}
        setApiKey={setApiKey}
        flowId={flowId}
        setFlowId={setFlowId}
      />

      <main className="max-w-6xl mx-auto px-4 pb-16">
        {phase === 'idle' && (
          <InputPanel
            documentName={documentName}
            setDocumentName={setDocumentName}
            documentText={documentText}
            setDocumentText={setDocumentText}
            onAudit={runAudit}
            mode={mode}
            apiKey={apiKey}
          />
        )}

        {phase === 'running' && (
          <ProgressStepper currentStep={currentStep} elapsed={elapsed} />
        )}

        {phase === 'error' && (
          <div className="mt-10 p-6 bg-[#da1e28]/10 border border-[#da1e28]/40 rounded-xl">
            <p className="text-[#ff8389] font-semibold text-lg mb-2">Koneksi Gagal</p>
            <p className="text-slate-300 text-sm mb-1 font-mono bg-slate-800 rounded px-3 py-2 leading-relaxed">{error}</p>
            <p className="text-slate-500 text-xs mt-3 mb-4">
              Pastikan Langflow Desktop berjalan, Flow sudah diimport, dan API Key sudah benar di panel Settings.
            </p>
            <div className="flex gap-2">
              <button
                onClick={reset}
                className="px-5 py-2 bg-[#0f62fe] hover:bg-[#0353e9] text-white rounded-lg text-sm font-medium transition-colors"
              >
                Coba Lagi
              </button>
              <button
                onClick={() => { reset(); setMode('demo'); }}
                className="px-5 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Kembali ke Demo Mode
              </button>
            </div>
          </div>
        )}

        {phase === 'done' && result && (
          <ResultsDashboard result={result} showToast={showToast} onReset={reset} />
        )}
      </main>
    </div>
  );
}
