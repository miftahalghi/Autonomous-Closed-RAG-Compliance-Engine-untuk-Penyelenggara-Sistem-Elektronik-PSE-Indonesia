import React, { useState } from 'react';
import { ShieldCheck, Zap, RefreshCw, Settings, X, Eye, EyeOff, CheckCircle } from 'lucide-react';

export default function Header({ mode, setMode, loadSample, onReset, apiKey, setApiKey, flowId, setFlowId }) {
  const [showSettings, setShowSettings] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [testStatus, setTestStatus] = useState(null); // null | 'testing' | 'ok' | 'fail'
  const [testMsg, setTestMsg] = useState('');

  const testConnection = async () => {
    setTestStatus('testing');
    setTestMsg('');
    try {
      const headers = {};
      if (apiKey.trim()) headers['x-api-key'] = apiKey.trim();
      const res = await fetch('/langflow/api/v1/flows', { headers });
      if (res.status === 401 || res.status === 403) {
        setTestStatus('fail');
        setTestMsg('API Key salah atau tidak valid (401/403).');
        return;
      }
      if (!res.ok) {
        setTestStatus('fail');
        setTestMsg(`Error ${res.status}: ${res.statusText}`);
        return;
      }
      const data = await res.json();
      const count = Array.isArray(data) ? data.length : (data?.flows?.length ?? '?');
      setTestStatus('ok');
      setTestMsg(`Terhubung! Ditemukan ${count} flow di Langflow Desktop.`);
    } catch (e) {
      setTestStatus('fail');
      setTestMsg(`Tidak dapat terhubung ke localhost:7860. Pastikan Langflow Desktop sedang berjalan.`);
    }
  };

  const hasKey = apiKey.trim().length > 0;

  return (
    <>
      <header className="bg-[#161616] border-b border-slate-700/60 sticky top-0 z-40 print:hidden">
        <div className="max-w-6xl mx-auto px-4 py-3">
          {/* Brand row */}
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 bg-[#0f62fe]/20 border border-[#0f62fe]/40 rounded-lg px-3 py-2">
                <ShieldCheck size={20} className="text-[#78a9ff]" />
                <span className="text-[#78a9ff] font-semibold text-sm tracking-wide">watsonx</span>
              </div>
              <div>
                <h1 className="text-white font-bold text-lg leading-tight tracking-tight">
                  Audit PDP Engine
                </h1>
                <p className="text-slate-400 text-xs leading-none mt-0.5">
                  Closed-RAG Legal Compliance Verifier · UU No. 27 Tahun 2022
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              {/* Mode toggle */}
              <div className="flex items-center gap-2 bg-slate-800 border border-slate-600 rounded-lg p-1">
                <button
                  onClick={() => setMode('demo')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all
                    ${mode === 'demo' ? 'bg-[#1192e8] text-white shadow' : 'text-slate-400 hover:text-white'}`}
                >
                  <Zap size={12} />
                  Offline Demo Mode
                </button>
                <button
                  onClick={() => setMode('live')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all
                    ${mode === 'live' ? 'bg-[#24a148] text-white shadow' : 'text-slate-400 hover:text-white'}`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${mode === 'live' ? 'bg-white animate-pulse' : 'bg-slate-500'}`} />
                  Live Endpoint (Langflow)
                </button>
              </div>

              {/* Settings button — shows badge if API key is set */}
              <button
                onClick={() => setShowSettings(true)}
                className={`relative flex items-center gap-1.5 px-3 py-2 text-xs border rounded-lg transition-colors
                  ${mode === 'live'
                    ? 'text-[#78a9ff] border-[#0f62fe]/50 hover:border-[#0f62fe] bg-[#0f62fe]/10'
                    : 'text-slate-400 hover:text-white border-slate-600 hover:border-slate-400'}`}
              >
                <Settings size={13} />
                Settings
                {hasKey && (
                  <span className="absolute -top-1 -right-1 w-2 h-2 bg-[#24a148] rounded-full" />
                )}
              </button>

              {onReset && (
                <button
                  onClick={onReset}
                  className="flex items-center gap-1.5 px-3 py-2 text-xs text-slate-400 hover:text-white border border-slate-600 hover:border-slate-400 rounded-lg transition-colors"
                >
                  <RefreshCw size={12} />
                  Audit Baru
                </button>
              )}
            </div>
          </div>

          {/* Quick Load row */}
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            <span className="text-slate-500 text-xs font-medium">Quick Load:</span>
            <button
              onClick={() => loadSample('critical')}
              className="px-3 py-1 text-xs bg-[#da1e28]/15 hover:bg-[#da1e28]/25 text-[#ff8389] border border-[#da1e28]/30 rounded-full transition-colors"
            >
              Sample PT Contoh Digital (Risiko Kritis: Pasal 46)
            </button>
            <button
              onClick={() => loadSample('compliant')}
              className="px-3 py-1 text-xs bg-[#24a148]/15 hover:bg-[#24a148]/25 text-[#42be65] border border-[#24a148]/30 rounded-full transition-colors"
            >
              Sample Compliant Policy
            </button>
            <button
              onClick={() => loadSample('minimal')}
              className="px-3 py-1 text-xs bg-slate-700/50 hover:bg-slate-700 text-slate-400 border border-slate-600 rounded-full transition-colors"
            >
              Sample Kosong / Minimalist
            </button>
          </div>
        </div>
      </header>

      {/* Settings modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm print:hidden">
          <div className="bg-[#161616] border border-slate-700 rounded-2xl shadow-2xl w-full max-w-lg mx-4">
            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
              <div className="flex items-center gap-2">
                <Settings size={16} className="text-[#78a9ff]" />
                <span className="text-white font-semibold text-sm">Konfigurasi Langflow Desktop</span>
              </div>
              <button onClick={() => { setShowSettings(false); setTestStatus(null); }} className="text-slate-400 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <div className="px-6 py-5 space-y-5">
              {/* Info banner */}
              <div className="bg-[#0f62fe]/10 border border-[#0f62fe]/30 rounded-lg px-4 py-3 text-xs text-[#82cfff] leading-relaxed">
                Langflow Desktop terdeteksi berjalan di <span className="font-mono font-bold">localhost:7860</span> (v1.11.0).
                Isi API Key dari Langflow Desktop untuk mengaktifkan Live Mode.
              </div>

              {/* API Key field */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  API Key Langflow
                  <span className="ml-2 text-slate-500 font-normal text-xs">
                    (Settings → API Keys di Langflow Desktop)
                  </span>
                </label>
                <div className="flex items-center gap-2 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 focus-within:border-[#0f62fe] transition-colors">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="flex-1 bg-transparent text-slate-100 text-sm font-mono outline-none placeholder:text-slate-500"
                  />
                  <button
                    onClick={() => setShowKey(!showKey)}
                    className="text-slate-400 hover:text-white ml-1"
                    tabIndex={-1}
                  >
                    {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                  {hasKey && <CheckCircle size={14} className="text-[#24a148]" />}
                </div>
                <p className="text-slate-500 text-xs mt-1.5">
                  Disimpan di <span className="font-mono">localStorage</span> browser. Tidak pernah dikirim ke server lain.
                </p>
              </div>

              {/* Flow ID field */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Flow ID
                  <span className="ml-2 text-slate-500 font-normal text-xs">
                    (dari URL saat flow dibuka di Langflow Desktop)
                  </span>
                </label>
                <input
                  type="text"
                  value={flowId}
                  onChange={(e) => setFlowId(e.target.value)}
                  placeholder="a98e2140-5b18-4d56-8e12-pdp272022flow"
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-slate-100 text-sm font-mono
                    outline-none focus:border-[#0f62fe] transition-colors placeholder:text-slate-500"
                />
                <p className="text-slate-500 text-xs mt-1.5">
                  Buka flow di Langflow Desktop → salin ID dari URL: <span className="font-mono">/flow/&#123;ID ini&#125;</span>
                </p>
              </div>

              {/* Test Connection */}
              <div className="border-t border-slate-700 pt-4">
                <div className="flex items-center gap-3">
                  <button
                    onClick={testConnection}
                    disabled={testStatus === 'testing'}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50
                      text-white text-xs font-medium rounded-lg transition-colors"
                  >
                    {testStatus === 'testing' ? (
                      <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-[#0f62fe]" />
                    )}
                    {testStatus === 'testing' ? 'Menguji koneksi...' : 'Test Koneksi'}
                  </button>

                  {testStatus === 'ok' && (
                    <span className="text-[#42be65] text-xs font-medium flex items-center gap-1.5">
                      <CheckCircle size={13} /> {testMsg}
                    </span>
                  )}
                  {testStatus === 'fail' && (
                    <span className="text-[#ff8389] text-xs">{testMsg}</span>
                  )}
                </div>
              </div>
            </div>

            {/* Modal footer */}
            <div className="px-6 py-4 border-t border-slate-700 flex justify-end">
              <button
                onClick={() => { setShowSettings(false); setTestStatus(null); }}
                className="px-5 py-2 bg-[#0f62fe] hover:bg-[#0353e9] text-white rounded-lg text-sm font-medium transition-colors"
              >
                Simpan & Tutup
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
