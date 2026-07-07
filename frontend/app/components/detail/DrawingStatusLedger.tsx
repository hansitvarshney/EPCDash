'use client';

import { FileCheck2 } from 'lucide-react';
import { DrawingStatusRow } from '../../lib/api';

const STATUS_CLASSES: Record<string, string> = {
  APPROVED: 'text-emerald-400 bg-emerald-950/30 border-emerald-900/40',
  PENDING: 'text-amber-400 bg-amber-950/30 border-amber-900/40',
  REJECTED: 'text-red-400 bg-red-950/30 border-red-900/40',
};

export default function DrawingStatusLedger({ rows }: { rows: DrawingStatusRow[] }) {
  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-5 py-3.5 border-b border-slate-800 bg-[#161F30]">
        <h3 className="font-bold text-white text-xs uppercase tracking-wide flex items-center gap-2">
          <FileCheck2 size={14} className="text-emerald-400" /> GFC Drawing Status Ledger
        </h3>
        <p className="text-[10px] text-slate-500 mt-0.5">Client sign-off compliance gate for the latest structural layouts.</p>
      </div>

      {rows.length === 0 ? (
        <div className="p-6 text-center">
          <p className="text-xs font-semibold text-slate-500">No drawings registered yet.</p>
        </div>
      ) : (
        <div className="divide-y divide-slate-800/60">
          {rows.map((row) => (
            <div key={row.drawing_number} className="px-5 py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-200 truncate">{row.drawing_number}</p>
                <p className="text-[10px] text-slate-500 mt-0.5 truncate">
                  {row.discipline || 'General'} &middot; Rev {row.gfc_revision || '—'}
                </p>
              </div>
              <span
                className={`text-[9px] font-bold uppercase tracking-wide px-2 py-0.5 rounded border shrink-0 ${
                  STATUS_CLASSES[row.client_signoff_status] ?? 'text-slate-400 bg-slate-800/50 border-slate-700'
                }`}
              >
                {row.client_signoff_status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
