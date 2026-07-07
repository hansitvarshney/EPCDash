'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, MapPin, Building2 } from 'lucide-react';
import {
  fetchSiteOverview,
  fetchExceptions,
  fetchDownloads,
  fetchAttendance,
  fetchSiteInsights,
  resolveException,
  deleteDocument,
  SiteOverview,
  ExceptionAlert,
  DownloadFile,
  AttendanceSheet as AttendanceSheetData,
  SiteInsights,
} from '../../lib/api';
import HealthBadge from '../../components/site/HealthBadge';
import VelocityTracker from '../../components/detail/VelocityTracker';
import ExceptionsFeed from '../../components/detail/ExceptionsFeed';
import DownloadHub from '../../components/detail/DownloadHub';
import IngestPanel from '../../components/detail/IngestPanel';
import DocumentChat from '../../components/chat/DocumentChat';
import ContractTimeline from '../../components/detail/ContractTimeline';
import SiteAttendanceSheet from '../../components/detail/SiteAttendanceSheet';
import PhysicalProgressTracker from '../../components/detail/PhysicalProgressTracker';
import PaymentMilestoneTracker from '../../components/detail/PaymentMilestoneTracker';
import MaterialVelocity from '../../components/detail/MaterialVelocity';
import LatestBillingActivity from '../../components/detail/LatestBillingActivity';
import FinancialLedger from '../../components/detail/FinancialLedger';
import DrawingStatusLedger from '../../components/detail/DrawingStatusLedger';

export default function SiteDetailPage() {
  const params = useParams();
  const siteId = Number(params.id);

  const [overview, setOverview] = useState<SiteOverview | null>(null);
  const [exceptions, setExceptions] = useState<ExceptionAlert[]>([]);
  const [downloads, setDownloads] = useState<DownloadFile[]>([]);
  const [attendance, setAttendance] = useState<AttendanceSheetData | null>(null);
  const [insights, setInsights] = useState<SiteInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [overviewData, exceptionsData, downloadsData, attendanceData, insightsData] = await Promise.all([
        fetchSiteOverview(siteId),
        fetchExceptions(siteId),
        fetchDownloads(siteId),
        fetchAttendance(siteId),
        fetchSiteInsights(siteId),
      ]);
      setOverview(overviewData);
      setExceptions(exceptionsData);
      setDownloads(downloadsData);
      setAttendance(attendanceData);
      setInsights(insightsData);
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

  const handleDeleteDownload = async (documentId: number) => {
    const previous = downloads;
    setDownloads((prev) => prev.filter((f) => f.document_id !== documentId));
    try {
      await deleteDocument(siteId, documentId);
    } catch {
      setDownloads(previous);
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

  const { site, velocity } = overview;

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

          <ContractTimeline timeline={overview.contract_timeline} metrics={overview.operational_metrics} />
        </div>

        {insights && (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            <PhysicalProgressTracker tracker={insights.milestone_tracker} siteId={siteId} onChanged={loadAll} />
            <PaymentMilestoneTracker tracker={insights.milestone_tracker} siteId={siteId} onChanged={loadAll} />
            <FinancialLedger ledger={insights.financial_ledger} />
            <MaterialVelocity rows={insights.material_velocity} />
            <LatestBillingActivity rows={insights.latest_billing_activity} />
            <DrawingStatusLedger rows={insights.drawing_status_ledger} />
          </div>
        )}

        {attendance && (
          <SiteAttendanceSheet
            siteId={siteId}
            attendance={attendance}
            todaysExpenseLog={insights?.financial_ledger.todays_expense_log ?? null}
            onExpenseSaved={loadAll}
          />
        )}

        <IngestPanel siteId={siteId} onIngested={loadAll} />

        <VelocityTracker velocity={velocity} />

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2">
            <ExceptionsFeed exceptions={exceptions} onResolve={handleResolve} />
          </div>
          <div className="space-y-6">
            <DownloadHub files={downloads} onDelete={handleDeleteDownload} />
          </div>
        </div>

        <DocumentChat siteId={siteId} />
      </div>
    </main>
  );
}
