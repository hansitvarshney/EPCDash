'use client';

import { Landmark, TrendingUp, TrendingDown } from 'lucide-react';
import { FinancialLedger as FinancialLedgerData } from '../../lib/api';

function formatCr(value: number): string {
  return `₹${(value / 10_000_000).toFixed(2)}Cr`;
}

export default function FinancialLedger({ ledger }: { ledger: FinancialLedgerData }) {
  const {
    total_invested_till_now,
    contract_value,
    pct_of_contract_invested,
    total_manual_daily_expenses,
    total_active_penalties,
    estimated_profit,
  } = ledger;
  const pctOfTenderValue =
    pct_of_contract_invested ?? (contract_value ? Math.min((total_invested_till_now / contract_value) * 100, 100) : 0);
  const isProfitPositive = estimated_profit != null && estimated_profit >= 0;

  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-5 py-3.5 border-b border-slate-800 bg-[#161F30]">
        <h3 className="font-bold text-white text-xs uppercase tracking-wide flex items-center gap-2">
          <Landmark size={14} className="text-amber-400" /> Project Financial Summary
        </h3>
        <p className="text-[10px] text-slate-500 mt-0.5">Real-time tracking of contract value, daily site expenses, and estimated project margins.</p>
      </div>

      <div className="p-5 space-y-4">
        {estimated_profit != null && (
          <div className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${
            isProfitPositive ? 'bg-emerald-950/20 border-emerald-900/40' : 'bg-red-950/20 border-red-900/40'
          }`}>
            <div className={`p-2 rounded-lg shrink-0 ${isProfitPositive ? 'bg-emerald-950/40 text-emerald-400' : 'bg-red-950/40 text-red-400'}`}>
              {isProfitPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Estimated Profit</p>
              <p className={`text-lg font-black mt-0.5 ${isProfitPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                {formatCr(estimated_profit)}
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Invested Till Now</p>
            <p className="text-lg font-black text-white mt-1">{formatCr(total_invested_till_now)}</p>
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Tender Value</p>
            <p className="text-lg font-black text-slate-300 mt-1">{contract_value != null ? formatCr(contract_value) : '—'}</p>
          </div>
        </div>

        <div>
          <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
            <div className="h-full rounded-full bg-amber-500" style={{ width: `${pctOfTenderValue}%` }} />
          </div>
          <p className="text-[10px] text-slate-500 mt-1.5">{pctOfTenderValue.toFixed(1)}% of Tender Value allocated</p>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-3 border-t border-slate-800/60">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Less: Day-Expenses</p>
            <p className="text-xs font-bold text-slate-300 mt-1">{formatCr(total_manual_daily_expenses)}</p>
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Less: Active Penalties</p>
            <p className="text-xs font-bold text-slate-300 mt-1">{formatCr(total_active_penalties)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
