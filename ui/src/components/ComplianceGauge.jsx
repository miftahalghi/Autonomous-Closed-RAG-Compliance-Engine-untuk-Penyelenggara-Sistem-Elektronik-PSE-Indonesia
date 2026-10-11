import React from 'react';

function getScoreColor(score) {
  if (score >= 80) return { stroke: '#24a148', text: '#42be65', label: 'Kepatuhan Tinggi', bg: '#24a148' };
  if (score >= 50) return { stroke: '#f1c21b', text: '#f1c21b', label: 'Kepatuhan Parsial', bg: '#f1c21b' };
  return { stroke: '#da1e28', text: '#ff8389', label: 'Risiko Kritis', bg: '#da1e28' };
}

export default function ComplianceGauge({ score }) {
  const { stroke, text, label } = getScoreColor(score);
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-36 h-36">
        <svg viewBox="0 0 130 130" className="w-full h-full -rotate-90">
          {/* Background track */}
          <circle
            cx="65" cy="65" r={radius}
            fill="none"
            stroke="#1e293b"
            strokeWidth="10"
          />
          {/* Progress arc */}
          <circle
            cx="65" cy="65" r={radius}
            fill="none"
            stroke={stroke}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-bold text-3xl leading-none" style={{ color: text }}>
            {score}
          </span>
          <span className="text-slate-400 text-xs mt-0.5">/ 100</span>
        </div>
      </div>
      <span className="text-xs font-semibold mt-1" style={{ color: text }}>{label}</span>
    </div>
  );
}
