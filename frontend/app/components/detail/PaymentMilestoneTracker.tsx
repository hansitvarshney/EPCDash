'use client';

import { useState } from 'react';
import { Receipt, Loader2 } from 'lucide-react';
import { MilestoneTracker as MilestoneTrackerData, PaymentMilestoneRow, updatePaymentMilestoneStatus } from '../../lib/api';

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr.length <= 10 ? `${dateStr}T00:00:00` : dateStr);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatCurrency(amount: number): string {
  return `₹${amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

const STATUS_STYLES: Record<PaymentMilestoneRow['status'], string> = {
  LOCKED: 'bg-slate-800/60 border-slate-700 text-slate-400',
  ELIGIBLE: 'bg-cyan-950/30 border-cyan-800/50 text-cyan-300',
  INVOICED: 'bg-amber-950/30 border-amber-800/50 text-amber-300',
  PAID: 'bg-emerald-950/30 border-emerald-800/50 text-emerald-300',
};

function PaymentMilestoneCard({
  bill,
  siteId,
  onChanged,
}: {
  bill: PaymentMilestoneRow;
  siteId: number;
  onChanged?: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTransition = async (status: 'INVOICED' | 'PAID') => {
    setSaving(true);
    setError(null);
    try {
      await updatePaymentMilestoneStatus(siteId, bill.id, status);
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-[#0B0F19] px-3.5 py-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs font-bold text-white truncate">{bill.bill_name}</p>
          {bill.linked_physical_milestone_name && (
            <p className="text-[10px] text-slate-500 mt-0.5 truncate">Linked: {bill.linked_physical_milestone_name}</p>
          )}
        </div>
        <span className={`text-[9px] font-bold uppercase tracking-wide px-2 py-1 rounded border shrink-0 ${STATUS_STYLES[bill.status]}`}>
          {bill.status}
        </span>
      </div>

      <div className="flex items-center justify-between mt-2">
        <span className="text-[11px] text-slate-500">{bill.contract_pct}% of contract value</span>
        <span className="text-sm font-black text-white">{formatCurrency(bill.bill_amount)}</span>
      </div>

      {(bill.status === 'ELIGIBLE' || bill.status === 'INVOICED') && (
        <div className="mt-2.5 flex items-center gap-2">
          {bill.status === 'ELIGIBLE' && (
            <button
              type="button"
              onClick={() => handleTransition('INVOICED')}
              disabled={saving}
              className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide px-2.5 py-1.5 rounded-md bg-cyan-700/80 hover:bg-cyan-600 text-white disabled:opacity-50"
            >
              {saving && <Loader2 size={11} className="animate-spin" />} Mark Invoiced
            </button>
          )}
          {bill.status === 'INVOICED' && (
            <button
              type="button"
              onClick={() => handleTransition('PAID')}
              disabled={saving}
              className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide px-2.5 py-1.5 rounded-md bg-emerald-700/80 hover:bg-emerald-600 text-white disabled:opacity-50"
            >
              {saving && <Loader2 size={11} className="animate-spin" />} Mark Paid
            </button>
          )}
        </div>
      )}

      {bill.status === 'PAID' && bill.paid_at && (
        <p className="text-[10px] text-emerald-500/80 font-semibold mt-2">Paid on {formatDate(bill.paid_at)}</p>
      )}

      {error && <p className="text-[10px] font-semibold text-red-400 mt-1.5">{error}</p>}
    </div>
  );
}

export default function PaymentMilestoneTracker({
  tracker,
  siteId,
  onChanged,
}: {
  tracker: MilestoneTrackerData;
  siteId: number;
  onChanged?: () => void;
}) {
  const { payment_milestones } = tracker;

  if (payment_milestones.length === 0) {
    return (
      <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
        <div className="px-5 py-3.5 border-b border-slate-800 bg-[#161F30]">
          <h3 className="font-bold text-white text-xs uppercase tracking-wide flex items-center gap-2">
            <Receipt size={14} className="text-cyan-400" /> Stage Payments / RA Bills
          </h3>
        </div>
        <div className="p-6 text-center">
          <p className="text-xs font-semibold text-slate-500">No stage payment schedule uploaded yet.</p>
          <p className="text-[10px] text-slate-600 mt-1">Upload a Tender Agreement or schedule workbook with RA Bill rows to populate this ledger.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-5 py-3.5 border-b border-slate-800 bg-[#161F30]">
        <h3 className="font-bold text-white text-xs uppercase tracking-wide flex items-center gap-2">
          <Receipt size={14} className="text-cyan-400" /> Stage Payments / RA Bills
        </h3>
        <p className="text-[10px] text-slate-500 mt-0.5">{payment_milestones.length} stage payment(s) tracked.</p>
      </div>

      <div className="p-5">
        <div className="space-y-2 max-h-96 overflow-y-auto pr-0.5">
          {payment_milestones.map((bill) => (
            <PaymentMilestoneCard key={bill.id} bill={bill} siteId={siteId} onChanged={onChanged} />
          ))}
        </div>
      </div>
    </div>
  );
}
