'use client';

import { useState } from 'react';
import { ShieldAlert, AlertTriangle, Info, CheckCircle2, FileSearch } from 'lucide-react';
import { ExceptionAlert, ExceptionSeverity } from '../../lib/api';
import ExceptionSourceModal from './ExceptionSourceModal';

const SEVERITY_CONFIG: Record<ExceptionSeverity, { Icon: typeof ShieldAlert; classes: string }> = {
  CRITICAL: { Icon: ShieldAlert, classes: 'text-red-400 bg-red-950/30 border-red-900/40' },
  WARNING: { Icon: AlertTriangle, classes: 'text-amber-400 bg-amber-950/30 border-amber-900/40' },
  INFO: { Icon: Info, classes: 'text-blue-400 bg-blue-950/30 border-blue-900/40' },
};

interface Props {
  exceptions: ExceptionAlert[];
  onResolve: (exceptionId: number) => void;
}

export default function ExceptionsFeed({ exceptions, onResolve }: Props) {
  const [selected, setSelected] = useState<ExceptionAlert | null>(null);

  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800 bg-[#161F30]">
        <h2 className="font-bold text-white text-sm uppercase tracking-wide flex items-center gap-2">
          <ShieldAlert size={15} className="text-red-400" /> Critical Exceptions Feed
        </h2>
        <p className="text-[11px] text-slate-500 mt-0.5">Flagged data anomalies caught by the Validation node, with full source-citation transparency.</p>
      </div>

      {exceptions.length === 0 ? (
        <div className="p-12 text-center">
          <CheckCircle2 size={28} className="mx-auto text-emerald-500 mb-3" />
          <p className="text-sm font-bold text-slate-300">No open exceptions.</p>
          <p className="text-xs text-slate-600 mt-1">Every ingested ledger entry has cleared validation.</p>
        </div>
      ) : (
        <div className="divide-y divide-slate-800/60">
          {exceptions.map((alert) => {
            const config = SEVERITY_CONFIG[alert.severity] ?? SEVERITY_CONFIG.INFO;
            const { Icon } = config;
            return (
              <div key={alert.id} className="p-5 flex items-start gap-4 hover:bg-slate-800/20 transition-colors">
                <div className={`shrink-0 p-2 rounded-lg border ${config.classes}`}>
                  <Icon size={15} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                      {alert.category}
                    </span>
                    <span className={`text-[9px] font-bold uppercase tracking-wider ${config.classes.split(' ')[0]}`}>{alert.severity}</span>
                    {alert.created_at && <span className="text-[10px] text-slate-600 font-mono">{alert.created_at.slice(0, 16).replace('T', ' ')}</span>}
                  </div>
                  <p className="text-sm text-slate-200 mt-1.5 leading-relaxed">{alert.message}</p>
                  <div className="flex items-center gap-3 mt-2.5">
                    <button
                      onClick={() => setSelected(alert)}
                      className="flex items-center gap-1.5 text-[11px] font-bold text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      <FileSearch size={12} /> View Source Citation
                    </button>
                    <button
                      onClick={() => onResolve(alert.id)}
                      className="text-[11px] font-bold text-slate-500 hover:text-emerald-400 transition-colors"
                    >
                      Mark Resolved
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selected && <ExceptionSourceModal alert={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
