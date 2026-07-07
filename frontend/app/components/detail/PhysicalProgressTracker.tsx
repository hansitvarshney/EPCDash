'use client';

import { useState } from 'react';
import { Milestone as MilestoneIcon, CheckCircle2, Circle, AlertTriangle, Loader2 } from 'lucide-react';
import { MilestoneTracker as MilestoneTrackerData, AllMilestoneRow, updateMilestoneStatus } from '../../lib/api';

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr.length <= 10 ? `${dateStr}T00:00:00` : dateStr);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

function MilestoneRow({
  milestone,
  siteId,
  onChanged,
}: {
  milestone: AllMilestoneRow;
  siteId: number;
  onChanged?: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isCompleted = milestone.status === 'COMPLETED';

  const handleToggle = async () => {
    setSaving(true);
    setError(null);
    try {
      await updateMilestoneStatus(siteId, milestone.id, isCompleted ? 'PENDING' : 'COMPLETED');
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex items-center gap-2.5 py-1.5">
      <button
        type="button"
        onClick={handleToggle}
        disabled={saving}
        title={isCompleted ? 'Mark as pending' : 'Mark as complete'}
        className="shrink-0 disabled:opacity-50"
      >
        {saving ? (
          <Loader2 size={15} className="animate-spin text-slate-500" />
        ) : isCompleted ? (
          <CheckCircle2 size={15} className="text-emerald-500" />
        ) : (
          <Circle size={15} className="text-slate-600 hover:text-slate-400" />
        )}
      </button>
      <span className={`text-xs truncate flex-1 ${isCompleted ? 'text-slate-300' : 'text-slate-400'}`}>
        {milestone.milestone_name}
      </span>
      <span className="text-[10px] text-slate-600 shrink-0">{formatDate(milestone.target_date)}</span>
      {error && <p className="text-[10px] font-semibold text-red-400 ml-2">{error}</p>}
    </div>
  );
}

export default function PhysicalProgressTracker({
  tracker,
  siteId,
  onChanged,
}: {
  tracker: MilestoneTrackerData;
  siteId: number;
  onChanged?: () => void;
}) {
  const { completed_count, total_count, next_milestone, is_lagging_schedule, all_milestones } = tracker;

  if (total_count === 0) {
    return (
      <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
        <div className="px-5 py-3.5 border-b border-slate-800 bg-[#161F30]">
          <h3 className="font-bold text-white text-xs uppercase tracking-wide flex items-center gap-2">
            <MilestoneIcon size={14} className="text-cyan-400" /> Physical Progress
          </h3>
        </div>
        <div className="p-6 text-center">
          <p className="text-xs font-semibold text-slate-500">No master schedule uploaded yet.</p>
          <p className="text-[10px] text-slate-600 mt-1">Upload a schedule workbook under the &quot;Micro-Schedule&quot; ingest category.</p>
        </div>
      </div>
    );
  }

  const overdue = next_milestone?.days_left != null && next_milestone.days_left < 0;

  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-5 py-3.5 border-b border-slate-800 bg-[#161F30] flex items-center justify-between">
        <div>
          <h3 className="font-bold text-white text-xs uppercase tracking-wide flex items-center gap-2">
            <MilestoneIcon size={14} className="text-cyan-400" /> Physical Progress
          </h3>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {completed_count} of {total_count} physical phase(s) complete.
          </p>
        </div>
        {is_lagging_schedule && (
          <span className="flex items-center gap-1 text-[9px] font-bold uppercase tracking-wide text-amber-400 bg-amber-950/30 border border-amber-900/40 px-2 py-1 rounded shrink-0">
            <AlertTriangle size={10} /> Lagging Baseline
          </span>
        )}
      </div>

      <div className="p-5 space-y-4">
        {next_milestone && (
          <div
            className={`rounded-lg border px-4 py-3 ${
              overdue ? 'bg-red-950/20 border-red-900/40' : is_lagging_schedule ? 'bg-amber-950/20 border-amber-900/40' : 'bg-[#0B0F19] border-slate-800'
            }`}
          >
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Next Milestone</p>
            <p className="text-sm font-bold text-white mt-1">{next_milestone.milestone_name}</p>
            <div className="flex items-center justify-between mt-1.5">
              <span className="text-[11px] text-slate-500">Target: {formatDate(next_milestone.target_date)}</span>
              <span className={`text-sm font-black ${overdue ? 'text-red-400' : 'text-cyan-400'}`}>
                {next_milestone.days_left != null ? `${Math.abs(next_milestone.days_left)}d ${overdue ? 'overdue' : 'left'}` : '—'}
              </span>
            </div>
          </div>
        )}

        {all_milestones.length > 0 && (
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
              All Phases <span className="normal-case text-slate-600">(tap to toggle manually)</span>
            </p>
            <div className="divide-y divide-slate-800/60 max-h-72 overflow-y-auto pr-0.5">
              {all_milestones.map((m) => (
                <MilestoneRow key={m.id} milestone={m} siteId={siteId} onChanged={onChanged} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
