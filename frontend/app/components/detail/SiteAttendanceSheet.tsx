'use client';

import { useMemo, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ClipboardList, Users, History, Download } from 'lucide-react';
import { AttendanceSheet, DailyExpenseLog, attendanceExportUrl } from '../../lib/api';
import PrincipalOverride from './PrincipalOverride';

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(`${dateStr}T00:00:00`);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', weekday: 'short' });
}

/** Monday-anchored ISO week start, used to bucket daily totals into weekly trend points. */
function weekStart(dateStr: string): string {
  const d = new Date(`${dateStr}T00:00:00`);
  const day = d.getDay();
  const diff = (day === 0 ? -6 : 1) - day; // shift back to Monday
  d.setDate(d.getDate() + diff);
  return d.toISOString().slice(0, 10);
}

function groupByWeek(rows: AttendanceSheet['historical_daily_totals']): { week: string; total_man_days: number }[] {
  const buckets = new Map<string, number>();
  for (const row of rows) {
    const key = weekStart(row.report_date);
    buckets.set(key, (buckets.get(key) ?? 0) + row.total_man_days);
  }
  return Array.from(buckets.entries())
    .sort(([a], [b]) => (a < b ? -1 : 1))
    .map(([week, total_man_days]) => ({
      week: new Date(`${week}T00:00:00`).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
      total_man_days,
    }));
}

type Tab = 'today' | 'historical';

interface SiteAttendanceSheetProps {
  siteId: number;
  attendance: AttendanceSheet;
  todaysExpenseLog?: DailyExpenseLog | null;
  onExpenseSaved?: () => void;
}

export default function SiteAttendanceSheet({ siteId, attendance, todaysExpenseLog = null, onExpenseSaved }: SiteAttendanceSheetProps) {
  const [tab, setTab] = useState<Tab>('today');
  const { current_date, current_day_entries, current_day_totals, historical_daily_totals } = attendance;

  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800 bg-[#161F30] flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="font-bold text-white text-sm uppercase tracking-wide flex items-center gap-2">
            <ClipboardList size={15} className="text-blue-400" /> Site Attendance Sheet
          </h2>
          <p className="text-[11px] text-slate-500 mt-0.5">Structured crew deployment, current day and lifetime log.</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1 bg-[#0B0F19] border border-slate-800 rounded-lg p-1">
            <TabButton active={tab === 'today'} onClick={() => setTab('today')} icon={Users} label="Today" />
            <TabButton active={tab === 'historical'} onClick={() => setTab('historical')} icon={History} label="Historical" />
          </div>
          <a
            href={attendanceExportUrl(siteId)}
            download
            className="flex items-center gap-1.5 text-[11px] font-bold text-white bg-emerald-600 hover:bg-emerald-500 px-3 py-2 rounded-lg transition-colors uppercase tracking-wide"
          >
            <Download size={12} /> Download Historical Attendance Sheet (Excel)
          </a>
        </div>
      </div>

      {tab === 'today' ? (
        <>
          <PrincipalOverride siteId={siteId} todaysExpenseLog={todaysExpenseLog} onSaved={onExpenseSaved} />
          <TodayTab currentDate={current_date} entries={current_day_entries} totals={current_day_totals} />
        </>
      ) : (
        <HistoricalTab rows={historical_daily_totals} />
      )}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: typeof Users;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-bold uppercase tracking-wide transition-colors ${
        active ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-slate-300'
      }`}
    >
      <Icon size={12} /> {label}
    </button>
  );
}

function TodayTab({
  currentDate,
  entries,
  totals,
}: {
  currentDate: string | null;
  entries: AttendanceSheet['current_day_entries'];
  totals: AttendanceSheet['current_day_totals'];
}) {
  if (!currentDate || entries.length === 0) {
    return (
      <div className="p-12 text-center">
        <p className="text-sm font-bold text-slate-300">No labor logged yet.</p>
        <p className="text-xs text-slate-600 mt-1">Ingest a Daily Progress Report to populate today&apos;s crew breakdown.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="px-6 pt-4 pb-1">
        <p className="text-[11px] font-bold text-slate-400">
          Latest reported date: <span className="text-white">{formatDate(currentDate)}</span>
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <th className="px-6 py-3">Contractor</th>
              <th className="px-4 py-3">Crew Type</th>
              <th className="px-4 py-3 text-right">Masons</th>
              <th className="px-4 py-3 text-right">Helpers</th>
              <th className="px-6 py-3">Assigned Activity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {entries.map((entry, idx) => (
              <tr key={idx} className="text-xs text-slate-200 hover:bg-slate-800/20 transition-colors">
                <td className="px-6 py-3 font-semibold">{entry.contractor_name}</td>
                <td className="px-4 py-3 text-slate-400">{entry.crew_type}</td>
                <td className="px-4 py-3 text-right font-mono">{entry.masons_count}</td>
                <td className="px-4 py-3 text-right font-mono">{entry.helpers_count}</td>
                <td className="px-6 py-3 text-slate-400">{entry.assigned_activity || '—'}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="text-xs font-black text-white bg-[#0B0F19] border-t border-slate-800">
              <td className="px-6 py-3" colSpan={2}>
                Total Deployed
              </td>
              <td className="px-4 py-3 text-right font-mono text-blue-400">{totals.masons}</td>
              <td className="px-4 py-3 text-right font-mono text-blue-400">{totals.helpers}</td>
              <td className="px-6 py-3 text-slate-400 font-semibold normal-case">{totals.total} total man-days</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

function HistoricalTab({ rows }: { rows: AttendanceSheet['historical_daily_totals'] }) {
  const weeklyData = useMemo(() => groupByWeek(rows), [rows]);

  if (rows.length === 0) {
    return (
      <div className="p-12 text-center">
        <p className="text-sm font-bold text-slate-300">No historical attendance data yet.</p>
        <p className="text-xs text-slate-600 mt-1">Man-day trends will appear here as DPRs are ingested over time.</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <p className="text-[11px] font-bold text-slate-400 mb-4">Weekly Total Man-Days Trend</p>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={weeklyData} margin={{ top: 5, right: 20, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
          <XAxis dataKey="week" tick={{ fill: '#64748B', fontSize: 10 }} />
          <YAxis tick={{ fill: '#64748B', fontSize: 10 }} />
          <Tooltip
            contentStyle={{ background: '#161F30', border: '1px solid #1F2937', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: '#94A3B8' }}
            cursor={{ fill: '#1F2937', opacity: 0.4 }}
          />
          <Bar dataKey="total_man_days" name="Total Man-Days" fill="#3B82F6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <p className="text-[10px] text-slate-600 mt-3">
        Weeks starting Monday, {rows.length} daily log{rows.length !== 1 ? 's' : ''} on record. Download the full raw ledger below for
        deep-history detail.
      </p>
    </div>
  );
}
