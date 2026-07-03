'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, MapPin, Building2 } from 'lucide-react';
import { fetchSiteOverview, fetchExceptions, fetchDownloads, resolveException, SiteOverview, ExceptionAlert, DownloadFile } from '../../lib/api';
import HealthBadge from '../../components/site/HealthBadge';
import VelocityTracker from '../../components/detail/VelocityTracker';
import ExceptionsFeed from '../../components/detail/ExceptionsFeed';
import DownloadHub from '../../components/detail/DownloadHub';
import IngestPanel from '../../components/detail/IngestPanel';
import DocumentChat from '../../components/chat/DocumentChat';

export default function SiteDetailPage() {
  const params = useParams();
  const siteId = Number(params.id);

  const [overview, setOverview] = useState<SiteOverview | null>(null);
  const [exceptions, setExceptions] = useState<ExceptionAlert[]>([]);
  const [downloads, setDownloads] = useState<DownloadFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [overviewData, exceptionsData, downloadsData] = await Promise.all([
        fetchSiteOverview(siteId),
        fetchExceptions(siteId),
        fetchDownloads(siteId),
      ]);
      setOverview(overviewData);
      setExceptions(exceptionsData);
      setDownloads(downloadsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load site data.');
    } finally {
      setLoading(false);
    }
  }, [siteId]);

  useEffect(() => {
    if (Number.isFinite(siteId)) loadAll();
  }, [siteId, loadAll]);

  const handleResolve = async (exceptionId: number) => {
    try {
      await resolveException(siteId, exceptionId);
      setExceptions((prev) => prev.filter((e) => e.id !== exceptionId));
    } catch {
      // no-op: keep it in the list if resolution failed
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-[#0B0F19] text-[#E2E8F0] p-10 flex items-center justify-center">
        <p className="text-slate-500 text-sm font-medium">Loading site detail...</p>
      </main>
    );
  }

  if (error || !overview) {
    return (
      <main className="min-h-screen bg-[#0B0F19] text-[#E2E8F0] p-10">
        <div className="max-w-3xl mx-auto bg-red-950/20 border border-red-900/40 rounded-xl p-8 text-center">
          <p className="text-red-400 font-bold text-sm">Could not load this site.</p>
          <p className="text-slate-500 text-xs mt-2">{error}</p>
          <Link href="/" className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-400 mt-4">
            <ArrowLeft size={12} /> Back to portfolio
          </Link>
        </div>
      </main>
    );
  }

  const { site, summary, velocity } = overview;

  return (
    <main className="min-h-screen bg-[#0B0F19] text-[#E2E8F0] p-6 lg:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        <Link href="/" className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-white transition-colors">
          <ArrowLeft size={12} /> Active Site Portfolio
        </Link>

        <div className="bg-[#111827] border border-slate-800/80 rounded-xl p-6 shadow-md">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <h1 className="text-xl lg:text-2xl font-black text-white">{site.name}</h1>
              <div className="flex flex-wrap items-center gap-4 mt-2">
                {site.location && (
                  <span className="flex items-center gap-1.5 text-xs text-slate-400">
                    <MapPin size={12} /> {site.location}
                  </span>
                )}
                {site.client_name && (
                  <span className="flex items-center gap-1.5 text-xs text-slate-400">
                    <Building2 size={12} /> {site.client_name}
                  </span>
                )}
              </div>
            </div>
            <HealthBadge status={site.health_status} />
          </div>

          <div className="grid grid-cols-3 gap-4 mt-6 pt-5 border-t border-slate-800/60">
            <Stat label="Masons Deployed" value={String(summary.manpower_deployed.cumulative_masons)} />
            <Stat label="Helpers Deployed" value={String(summary.manpower_deployed.cumulative_helpers)} />
            <Stat label="Total Man-Days" value={String(summary.manpower_deployed.total_man_days)} accent />
          </div>
        </div>

        <IngestPanel siteId={siteId} onIngested={loadAll} />

        <VelocityTracker velocity={velocity} />

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2">
            <ExceptionsFeed exceptions={exceptions} onResolve={handleResolve} />
          </div>
          <div className="space-y-6">
            <DownloadHub files={downloads} />
          </div>
        </div>

        <DocumentChat siteId={siteId} />
      </div>
    </main>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`text-2xl font-black mt-1 ${accent ? 'text-blue-400' : 'text-white'}`}>{value}</p>
    </div>
  );
}
