import Link from 'next/link';
import { MapPin, Building2, ArrowUpRight, IndianRupee } from 'lucide-react';
import { SiteCard as SiteCardType } from '../../lib/api';
import HealthBadge from './HealthBadge';

function formatCurrency(value: number): string {
  if (!value) return '—';
  if (value >= 10_000_000) return `₹${(value / 10_000_000).toFixed(1)} Cr`;
  if (value >= 100_000) return `₹${(value / 100_000).toFixed(1)} L`;
  return `₹${value.toLocaleString()}`;
}

export default function SiteCard({ site }: { site: SiteCardType }) {
  const totalOpen = site.open_exceptions.critical + site.open_exceptions.warning + site.open_exceptions.info;

  return (
    <Link
      href={`/sites/${site.id}`}
      className="group block bg-[#111827] border border-slate-800/80 hover:border-blue-700/60 rounded-xl p-6 shadow-md hover:shadow-xl transition-all"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-sm font-bold text-white leading-snug group-hover:text-blue-400 transition-colors">{site.name}</h3>
          {site.location && (
            <p className="flex items-center gap-1 text-[11px] text-slate-500 mt-1.5">
              <MapPin size={11} /> {site.location}
            </p>
          )}
          {site.client_name && (
            <p className="flex items-center gap-1 text-[11px] text-slate-500 mt-1">
              <Building2 size={11} /> {site.client_name}
            </p>
          )}
        </div>
        <ArrowUpRight size={18} className="text-slate-600 group-hover:text-blue-400 transition-colors shrink-0" />
      </div>

      <div className="mt-5 flex items-center justify-between">
        <HealthBadge status={site.health_status} />
        {totalOpen > 0 && (
          <span className="text-[10px] font-bold text-slate-400">
            {totalOpen} open exception{totalOpen !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <div className="mt-5 pt-4 border-t border-slate-800/80 grid grid-cols-2 gap-3 text-[11px]">
        <div>
          <p className="text-slate-500 uppercase tracking-wide font-bold text-[9px] mb-1 flex items-center gap-1">
            <IndianRupee size={9} /> Total Tender Value
          </p>
          <p className="text-slate-200 font-bold">{formatCurrency(site.total_tender_value)}</p>
        </div>
        <div>
          <p className="text-slate-500 uppercase tracking-wide font-bold text-[9px] mb-1">Last Synced</p>
          <p className="text-slate-200 font-bold font-mono">{site.last_synced_date || '—'}</p>
        </div>
      </div>
    </Link>
  );
}
