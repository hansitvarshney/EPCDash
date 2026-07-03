'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Gauge, TrendingUp } from 'lucide-react';
import { VelocityData } from '../../lib/api';

export default function VelocityTracker({ velocity }: { velocity: VelocityData }) {
  const hasSeries = velocity.series.length > 0;
  const variance =
    velocity.latest_actual_progress_pct != null && velocity.schedule_baseline_pct != null
      ? velocity.latest_actual_progress_pct - velocity.schedule_baseline_pct
      : null;

  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800 bg-[#161F30] flex items-center justify-between">
        <div>
          <h2 className="font-bold text-white text-sm uppercase tracking-wide flex items-center gap-2">
            <Gauge size={15} className="text-blue-400" /> Timeline & Progress Velocity
          </h2>
          <p className="text-[11px] text-slate-500 mt-0.5">Schedule completion baseline vs. active field-reported progress.</p>
        </div>
        {variance !== null && (
          <div className={`flex items-center gap-1.5 text-xs font-bold ${variance >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            <TrendingUp size={13} />
            {variance >= 0 ? '+' : ''}
            {variance.toFixed(1)}% vs. baseline
          </div>
        )}
      </div>

      <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-4 border-b border-slate-800/60">
        <Stat label="Schedule Baseline" value={velocity.schedule_baseline_pct != null ? `${velocity.schedule_baseline_pct.toFixed(1)}%` : '—'} />
        <Stat label="Latest Actual Progress" value={velocity.latest_actual_progress_pct != null ? `${velocity.latest_actual_progress_pct.toFixed(1)}%` : '—'} accent />
        <Stat label="Data Points" value={String(velocity.series.length)} />
      </div>

      <div className="p-6">
        {hasSeries ? (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={velocity.series} margin={{ top: 5, right: 20, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
              <XAxis dataKey="report_date" tick={{ fill: '#64748B', fontSize: 10 }} />
              <YAxis tick={{ fill: '#64748B', fontSize: 10 }} unit="%" />
              <Tooltip
                contentStyle={{ background: '#161F30', border: '1px solid #1F2937', borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: '#94A3B8' }}
              />
              {velocity.schedule_baseline_pct != null && (
                <ReferenceLine y={velocity.schedule_baseline_pct} stroke="#F59E0B" strokeDasharray="4 4" label={{ value: 'Baseline', fill: '#F59E0B', fontSize: 10, position: 'insideTopRight' }} />
              )}
              <Line type="monotone" dataKey="actual_progress_pct" name="Actual Progress" stroke="#3B82F6" strokeWidth={2.5} dot={{ r: 3, fill: '#3B82F6' }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-16 text-slate-600 text-xs font-medium">
            No structural progress % data points yet — ingest a Daily Progress Report to populate this tracker.
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`text-xl font-black mt-1 ${accent ? 'text-blue-400' : 'text-white'}`}>{value}</p>
    </div>
  );
}
