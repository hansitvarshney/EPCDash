'use client';

import { useState } from 'react';
import { ShieldCheck, Check, Loader2 } from 'lucide-react';
import { DailyExpenseLog, saveDailyExpenseLog } from '../../lib/api';

interface Props {
  siteId: number;
  todaysExpenseLog: DailyExpenseLog | null;
  onSaved?: () => void;
}

export default function PrincipalOverride({ siteId, todaysExpenseLog, onSaved }: Props) {
  const [laborWages, setLaborWages] = useState(todaysExpenseLog?.labor_wages_paid?.toString() ?? '');
  const [miscExpenses, setMiscExpenses] = useState(todaysExpenseLog?.misc_expenses_paid?.toString() ?? '');
  const [miscNotes, setMiscNotes] = useState(todaysExpenseLog?.misc_expenses_notes ?? '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await saveDailyExpenseLog(siteId, {
        labor_wages_paid: laborWages.trim() === '' ? undefined : Number(laborWages),
        misc_expenses_paid: miscExpenses.trim() === '' ? undefined : Number(miscExpenses),
        misc_expenses_notes: miscNotes.trim() === '' ? undefined : miscNotes.trim(),
      });
      setSaved(true);
      onSaved?.();
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save daily logs.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-6 mt-4 mb-2 bg-[#0B0F19] border border-amber-900/40 rounded-lg px-5 py-4">
      <div className="flex items-center gap-2 mb-3">
        <ShieldCheck size={14} className="text-amber-400" />
        <p className="text-xs font-bold text-white uppercase tracking-wide">Principal Override</p>
        <p className="text-[10px] text-slate-500 font-medium">Lock in today&apos;s true site cash outflows</p>
      </div>

      <div className="flex flex-col sm:flex-row items-stretch sm:items-end gap-3">
        <div className="flex-1 min-w-0">
          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
            Today&apos;s Total Labor Wages
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-500 font-semibold">₹</span>
            <input
              type="number"
              inputMode="decimal"
              value={laborWages}
              onChange={(e) => setLaborWages(e.target.value)}
              placeholder="0"
              className="w-full bg-[#111827] border border-slate-800 rounded-lg pl-7 pr-3 py-2 text-sm font-semibold text-white focus:outline-none focus:border-amber-700/60"
            />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
            Today&apos;s Miscellaneous Expenses
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-500 font-semibold">₹</span>
            <input
              type="number"
              inputMode="decimal"
              value={miscExpenses}
              onChange={(e) => setMiscExpenses(e.target.value)}
              placeholder="0"
              className="w-full bg-[#111827] border border-slate-800 rounded-lg pl-7 pr-3 py-2 text-sm font-semibold text-white focus:outline-none focus:border-amber-700/60"
            />
          </div>
        </div>

        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className={`flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wide transition-colors shrink-0 ${
            saved ? 'bg-emerald-600 text-white' : 'bg-amber-600 hover:bg-amber-500 text-white disabled:opacity-50'
          }`}
        >
          {saving ? <Loader2 size={13} className="animate-spin" /> : saved ? <Check size={13} /> : null}
          {saving ? 'Saving...' : saved ? 'Saved' : 'Save Daily Logs'}
        </button>
      </div>

      <div className="mt-3">
        <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
          Expense Notes <span className="normal-case font-medium text-slate-600">(optional context for misc. costs)</span>
        </label>
        <input
          type="text"
          value={miscNotes}
          onChange={(e) => setMiscNotes(e.target.value)}
          placeholder="e.g., Diesel, equipment rental, local clearance"
          className="w-full bg-[#111827] border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-700/60"
        />
      </div>

      {error && <p className="text-[11px] font-semibold text-red-400 mt-2">{error}</p>}
    </div>
  );
}
