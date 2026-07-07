'use client';

import { Gauge } from 'lucide-react';
import { MaterialVelocityRow } from '../../lib/api';

export default function MaterialVelocity({ rows }: { rows: MaterialVelocityRow[] }) {
  const visible = rows.slice(0, 6);

  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-5 py-3.5 border-b border-slate-800 bg-[#161F30]">
        <h3 className="font-bold text-white text-xs uppercase tracking-wide flex items-center gap-2">
          <Gauge size={14} className="text-purple-400" /> Material Velocity
        </h3>
        <p className="text-[10px] text-slate-500 mt-0.5">Consumption vs. BOQ allocation, highest-risk first.</p>
      </div>

      {visible.length === 0 ? (
        <div className="p-6 text-center">
          <p className="text-xs font-semibold text-slate-500">No material ledger entries yet.</p>
        </div>
      ) : (
        <div className="divide-y divide-slate-800/60 max-h-64 overflow-y-auto">
          {visible.map((row) => {
            const overAllocated = (row.pct_of_boq ?? 0) > 100;
            return (
              <div key={row.material_name} className={`px-5 py-2.5 ${overAllocated ? 'bg-red-950/10' : ''}`}>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-slate-200 truncate">{row.material_name}</span>
                  <span className={`text-xs font-black shrink-0 ${overAllocated ? 'text-red-400' : 'text-slate-300'}`}>
                    {row.pct_of_boq != null ? `${row.pct_of_boq}%` : '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-2 mt-1">
                  <span className="text-[10px] text-slate-500">
                    Yesterday: {row.consumed_yesterday.toLocaleString()} {row.unit}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    Till now: {row.consumed_till_now.toLocaleString()} {row.unit}
                  </span>
                </div>
                <div className="h-1 rounded-full bg-slate-800 overflow-hidden mt-1.5">
                  <div
                    className={`h-full rounded-full ${overAllocated ? 'bg-red-500' : 'bg-purple-500'}`}
                    style={{ width: `${Math.min(row.pct_of_boq ?? 0, 100)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
