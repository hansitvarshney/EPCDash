'use client';

import React, { useEffect, useState } from 'react';
import { LayoutGrid, RefreshCcw } from 'lucide-react';
import { fetchSites, SiteCard as SiteCardType } from './lib/api';
import SiteCard from './components/site/SiteCard';

export default function Home() {
  const [sites, setSites] = useState<SiteCardType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSites = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSites();
      setSites(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reach the platform API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSites();
  }, []);

  const counts = sites.reduce(
    (acc, s) => {
      acc[s.health_status] = (acc[s.health_status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <main className="min-h-screen bg-[#0B0F19] text-[#E2E8F0] p-6 lg:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-[#111827] p-6 rounded-xl border border-slate-800/80 shadow-md">
          <div>
            <p className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-blue-400 mb-1.5">
              <LayoutGrid size={12} /> Executive Reaction Center
            </p>
            <h1 className="text-xl lg:text-2xl font-black tracking-tight text-white">Active Site Portfolio</h1>
            <p className="text-xs lg:text-sm text-slate-400 font-medium mt-1">
              Real-time operational health across every turnkey EPC site under management.
            </p>
          </div>
          <button
            onClick={loadSites}
            className="flex items-center gap-2 self-start md:self-auto text-xs font-bold uppercase tracking-wide text-slate-300 bg-slate-800/60 hover:bg-slate-800 border border-slate-700 px-4 py-2.5 rounded-lg transition-colors"
          >
            <RefreshCcw size={13} /> Refresh
          </button>
        </div>

        {!loading && !error && sites.length > 0 && (
          <div className="grid grid-cols-3 gap-4">
            <SummaryChip label="On Track" value={counts.ON_TRACK || 0} color="text-emerald-400" />
            <SummaryChip label="At Risk" value={counts.AT_RISK || 0} color="text-amber-400" />
            <SummaryChip label="Action Required" value={counts.ACTION_REQUIRED || 0} color="text-red-400" />
          </div>
        )}

        {loading && (
          <div className="text-center py-24 text-slate-500 text-sm font-medium">Loading active site portfolio...</div>
        )}

        {!loading && error && (
          <div className="bg-red-950/20 border border-red-900/40 rounded-xl p-8 text-center">
            <p className="text-red-400 font-bold text-sm">Could not reach the platform API.</p>
            <p className="text-slate-500 text-xs mt-2">{error}</p>
            <p className="text-slate-600 text-[11px] mt-3">Ensure the backend is running at the configured API base URL.</p>
          </div>
        )}

        {!loading && !error && sites.length === 0 && (
          <div className="bg-[#111827] border border-slate-800/80 rounded-xl p-16 text-center">
            <p className="text-slate-400 font-bold text-sm">No active sites yet.</p>
            <p className="text-slate-600 text-xs mt-2">Seed demo data or ingest a document to get started.</p>
          </div>
        )}

        {!loading && !error && sites.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {sites.map((site) => (
              <SiteCard key={site.id} site={site} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

function SummaryChip({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl px-5 py-4">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`text-2xl font-black mt-1 ${color}`}>{value}</p>
    </div>
  );
}
