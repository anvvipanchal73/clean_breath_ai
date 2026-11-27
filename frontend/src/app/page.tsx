'use client';

import React, { useEffect, useState } from 'react';

export default function Home() {
  const [aqi, setAqi] = useState(196);
  const [location, setLocation] = useState('Delhi (NCR) · Dwarka');
  const [language, setLanguage] = useState<'en' | 'hi'>('en');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center p-4">
      <div className="w-full max-w-md bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6 shadow-2xl mt-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌬️</span>
            <div>
              <h1 className="font-bold text-lg leading-tight">CleanBreath AI</h1>
              <p className="text-xs text-slate-400">Family Pollution Defense</p>
            </div>
          </div>
          <button
            onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')}
            className="px-3 py-1 bg-white/5 border border-white/10 rounded-full text-xs font-semibold hover:bg-white/10 transition"
          >
            🌐 {language.toUpperCase()}
          </button>
        </div>

        {/* Hero AQI Card */}
        <div className="text-center p-6 bg-red-500/10 border border-red-500/30 rounded-2xl mb-6 shadow-inner">
          <div className="text-xs font-semibold text-slate-400 mb-1">📍 {location}</div>
          <div className="text-6xl font-extrabold text-white tracking-tight my-2">{aqi}</div>
          <div className="inline-block px-3 py-1 bg-red-500/20 text-red-400 border border-red-500/40 rounded-full text-xs font-bold mb-3">
            ⚠️ Hazardous / Severe (Red)
          </div>
          <p className="text-xs text-slate-300 leading-relaxed max-w-xs mx-auto">
            {language === 'en'
              ? 'Unhealthy air. Avoid outdoor runs. Keep windows sealed and operate room air purifiers.'
              : 'खराब हवा। बाहरी व्यायाम न करें। खिड़कियाँ बंद रखें और शोधक चलाएं।'}
          </p>
        </div>

        {/* Live Metrics */}
        <div className="grid grid-cols-3 gap-2 mb-6">
          <div className="bg-white/5 border border-white/10 rounded-xl p-3 text-center">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">PM2.5</div>
            <div className="text-lg font-bold text-sky-400">41</div>
            <div className="text-[10px] text-slate-500">µg/m³</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-xl p-3 text-center">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">PM10</div>
            <div className="text-lg font-bold text-sky-400">43</div>
            <div className="text-[10px] text-slate-500">µg/m³</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-xl p-3 text-center">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Inversion</div>
            <div className="text-lg font-bold text-emerald-400">Low</div>
            <div className="text-[10px] text-slate-500">Risk</div>
          </div>
        </div>

        {/* Quantified Impact Showcase */}
        <div className="border-t border-white/10 pt-4 mb-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            Today's Quantified Avoidance
          </h2>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <div className="text-sky-400 font-extrabold text-lg">235 µg</div>
              <div className="text-[11px] text-slate-400">PM2.5 saved (Metro)</div>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <div className="text-sky-400 font-extrabold text-lg">2.4 kg</div>
              <div className="text-[11px] text-slate-400">CO₂ avoided</div>
            </div>
          </div>
        </div>

        {/* Timeline Routine */}
        <div className="border-t border-white/10 pt-4 mb-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            Tailored Routine
          </h2>
          <div className="space-y-2">
            <div className="bg-white/5 border-l-4 border-red-500 rounded-xl p-3 text-xs">
              <div className="flex justify-between text-slate-400 font-semibold mb-1">
                <span>06:30 – 07:30</span>
                <span className="text-red-400 font-bold">AVOID</span>
              </div>
              <div className="font-bold text-white text-sm mb-1">Keep Windows Sealed</div>
              <p className="text-slate-400 leading-normal">
                Morning smog is trapped near ground level by thermal inversion. Run air purifier.
              </p>
            </div>

            <div className="bg-white/5 border-l-4 border-emerald-500 rounded-xl p-3 text-xs">
              <div className="flex justify-between text-slate-400 font-semibold mb-1">
                <span>08:30 – 09:30</span>
                <span className="text-emerald-400 font-bold">DO</span>
              </div>
              <div className="font-bold text-white text-sm mb-1">Take Metro & Wear N95 Mask</div>
              <p className="text-slate-400 leading-normal">
                Enclosed transit with air filtration cuts inhaled particulate matter significantly.
              </p>
            </div>
          </div>
        </div>

        {/* Medical disclaimer */}
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-[11px] text-amber-200 leading-relaxed">
          ⚠️ <strong>Medical Note:</strong> General guidance only. If experiencing chest tightness or breathlessness, seek immediate medical attention.
        </div>
      </div>
    </div>
  );
}
