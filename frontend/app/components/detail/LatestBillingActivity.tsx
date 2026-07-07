'use client';

import { Receipt } from 'lucide-react';
import { BillingActivityRow } from '../../lib/api';

const STATUS_CLASSES: Record<string, string> = {
  EXCEPTION_FLAGGED: 'text-red-400 bg-red-950/30 border-red-900/40',
  OVERDUE: 'text-red-400 bg-red-950/30 border-red-900/40',
  PENDING: 'text-amber-400 bg-amber-950/30 border-amber-900/40',
  APPROVED: 'text-blue-400 bg-blue-950/30 border-blue-900/40',
  PAID: 'text-emerald-400 bg-emerald-950/30 border-emerald-900/40',
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(`${dateStr}T00:00:00`);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
}

export default function LatestBillingActivity({ rows }: { rows: BillingActivityRow[] }) {
  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-5 py-3.5 border-b border-slate-800 bg-[#161F30]">
        <h3 className="font-bold text-white text-xs uppercase tracking-wide flex items-center gap-2">
          <Receipt size={14} className="text-blue-400" /> Latest Billing Activity
        </h3>
        <p className="text-[10px] text-slate-500 mt-0.5">Most recent vendor invoices and their processing status.</p>
      </div>

      {rows.length === 0 ? (
        <div className="p-6 text-center">
          <p className="text-xs font-semibold text-slate-500">No invoices recorded yet.</p>
        </div>
      ) : (
        <div className="divide-y divide-slate-800/60">
          {rows.map((row, idx) => (
            <div key={idx} className="px-5 py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-200 truncate">{row.vendor_name}</p>
                <p className="text-[10px] text-slate-500 mt-0.5">
                  {row.invoice_number || 'No invoice #'} &middot; {formatDate(row.invoice_date)}
                </p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs font-black text-white">₹{(row.invoice_amount / 100_000).toFixed(2)}L</p>
                <span
                  className={`inline-block mt-1 text-[9px] font-bold uppercase tracking-wide px-2 py-0.5 rounded border ${
                    STATUS_CLASSES[row.status] ?? 'text-slate-400 bg-slate-800/50 border-slate-700'
                  }`}
                >
                  {row.status.replace('_', ' ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
