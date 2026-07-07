'use client';

import { CalendarClock, CalendarCheck, TimerReset, Wallet, HandCoins } from 'lucide-react';
import { ContractTimeline as ContractTimelineData, OperationalMetrics } from '../../lib/api';

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(`${dateStr}T00:00:00`);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

interface Props {
  timeline: ContractTimelineData;
  metrics: OperationalMetrics;
}

export default function ContractTimeline({ timeline, metrics }: Props) {
  const { tender_invoiced_rate, uninvoiced_work_value } = metrics;

  return (
    <div className="mt-6 pt-5 border-t border-slate-800/60">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <TimelineStat icon={CalendarClock} label="Contract Start" value={formatDate(timeline.start_date)} />
        <TimelineStat icon={CalendarCheck} label="Target End Date" value={formatDate(timeline.target_end_date)} />
        <TimelineStat
          icon={TimerReset}
          label={timeline.is_overdue ? 'Days Overdue' : 'Days Remaining'}
          value={timeline.days_remaining != null ? String(Math.abs(timeline.days_remaining)) : '—'}
          accent={timeline.is_overdue ? 'red' : 'blue'}
        />
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Schedule Elapsed</p>
          <div className="flex items-center gap-2 mt-1.5">
            <div className="flex-1 h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className={`h-full rounded-full ${timeline.is_overdue ? 'bg-red-500' : 'bg-blue-500'}`}
                style={{ width: `${Math.min(timeline.pct_elapsed ?? 0, 100)}%` }}
              />
            </div>
            <span className="text-xs font-black text-white shrink-0">
              {timeline.pct_elapsed != null ? `${timeline.pct_elapsed}%` : '—'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-5">
        <div className="flex items-center gap-3 bg-[#0B0F19] border border-slate-800/80 rounded-lg px-4 py-3">
          <div className="p-2 rounded-lg bg-amber-950/30 border border-amber-900/40 text-amber-400 shrink-0">
            <Wallet size={14} />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Tender Invoiced Rate</p>
            <p className="text-sm font-black text-white mt-0.5">
              {tender_invoiced_rate.invoiced_pct != null ? `${tender_invoiced_rate.invoiced_pct}%` : '—'}
              <span className="text-[11px] font-semibold text-slate-500 ml-1.5">
                {tender_invoiced_rate.contract_value != null
                  ? `₹${(tender_invoiced_rate.invoiced_amount / 10_000_000).toFixed(2)}Cr of ₹${(tender_invoiced_rate.contract_value / 10_000_000).toFixed(2)}Cr claimed`
                  : 'of total tender value claimed'}
              </span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 bg-[#0B0F19] border border-slate-800/80 rounded-lg px-4 py-3">
          <div className="p-2 rounded-lg bg-purple-950/30 border border-purple-900/40 text-purple-400 shrink-0">
            <HandCoins size={14} />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Uninvoiced Work Value</p>
            {uninvoiced_work_value.uninvoiced_amount > 0 ? (
              <>
                <p className="text-sm font-black text-white mt-0.5">
                  ₹{(uninvoiced_work_value.uninvoiced_amount / 10_000_000).toFixed(2)}Cr Earned
                </p>
                <p className="text-[11px] font-semibold text-slate-500 mt-0.5 truncate">
                  Work executed on-site awaiting the next RA Bill submission cycle.
                </p>
              </>
            ) : (
              <p className="text-sm font-black text-emerald-400 mt-0.5">All eligible work invoiced</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function TimelineStat({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: typeof CalendarClock;
  label: string;
  value: string;
  accent?: 'blue' | 'red';
}) {
  return (
    <div>
      <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500">
        <Icon size={11} /> {label}
      </p>
      <p
        className={`text-xl font-black mt-1 ${
          accent === 'red' ? 'text-red-400' : accent === 'blue' ? 'text-blue-400' : 'text-white'
        }`}
      >
        {value}
      </p>
    </div>
  );
}
