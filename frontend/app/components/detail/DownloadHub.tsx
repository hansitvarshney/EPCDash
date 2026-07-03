'use client';

import { useMemo, useState } from 'react';
import { Download, FileSpreadsheet, Calendar, ChevronDown, Trash2 } from 'lucide-react';
import { DownloadFile, downloadFileUrl } from '../../lib/api';

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const CATEGORY_LABELS: Record<string, string> = {
  DPR: 'Daily Progress Log',
  MATERIAL: 'Material Ledger',
  BILLING: 'Billing Tracker',
  DRAWING: 'Drawing Log',
};

const UNDATED_GROUP = 'Undated';

function parseReportDate(dateStr: string | null): Date | null {
  if (!dateStr) return null;
  const d = new Date(`${dateStr}T00:00:00`);
  return Number.isNaN(d.getTime()) ? null : d;
}

function monthYearLabel(dateStr: string | null): string {
  const d = parseReportDate(dateStr);
  return d ? d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : UNDATED_GROUP;
}

function formatReportDate(dateStr: string | null): string {
  const d = parseReportDate(dateStr);
  return d ? d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Unknown';
}

interface DownloadHubProps {
  files: DownloadFile[];
  onDelete: (documentId: number) => void;
}

export default function DownloadHub({ files, onDelete }: DownloadHubProps) {
  const sortedFiles = useMemo(
    () =>
      [...files].sort((a, b) => {
        const dateA = parseReportDate(a.report_date)?.getTime() ?? 0;
        const dateB = parseReportDate(b.report_date)?.getTime() ?? 0;
        return dateB - dateA;
      }),
    [files]
  );

  const groups = useMemo(() => {
    const map = new Map<string, DownloadFile[]>();
    for (const file of sortedFiles) {
      const key = monthYearLabel(file.report_date);
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(file);
    }
    return Array.from(map.entries());
  }, [sortedFiles]);

  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  const toggleGroup = (key: string) => {
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800 bg-[#161F30]">
        <h2 className="font-bold text-white text-sm uppercase tracking-wide flex items-center gap-2">
          <FileSpreadsheet size={15} className="text-emerald-400" /> Download Hub
        </h2>
        <p className="text-[11px] text-slate-500 mt-0.5">Generated tracking sheets, grouped by report month.</p>
      </div>

      {groups.length === 0 ? (
        <div className="p-10 text-center text-xs text-slate-600 font-medium">No tracking sheets generated yet for this site.</div>
      ) : (
        <div className="divide-y divide-slate-800/60">
          {groups.map(([groupLabel, groupFiles], groupIdx) => {
            const isCollapsed = collapsed[groupLabel] ?? groupIdx !== 0;
            return (
              <div key={groupLabel}>
                <button
                  type="button"
                  onClick={() => toggleGroup(groupLabel)}
                  className="w-full flex items-center justify-between gap-2 px-6 py-3 bg-[#0F1524] hover:bg-[#141B2E] transition-colors"
                >
                  <span className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-slate-300">
                    <Calendar size={12} className="text-slate-500" /> {groupLabel}
                    <span className="text-slate-600 font-medium normal-case">({groupFiles.length})</span>
                  </span>
                  <ChevronDown size={14} className={`text-slate-500 transition-transform ${isCollapsed ? '' : 'rotate-180'}`} />
                </button>

                {!isCollapsed && (
                  <div className="divide-y divide-slate-800/60">
                    {groupFiles.map((file) => (
                      <div
                        key={file.document_id}
                        className="p-4 pl-6 flex items-center justify-between gap-4 hover:bg-slate-800/20 transition-colors"
                      >
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-slate-200 truncate">{CATEGORY_LABELS[file.category] || file.category}</p>
                          <p className="text-[10px] text-slate-400 mt-1 font-semibold">Report Date: {formatReportDate(file.report_date)}</p>
                          <p className="text-[10px] text-slate-600 mt-0.5">
                            Synced {file.last_synced_at} &middot; {formatSize(file.size_bytes)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <a
                            href={downloadFileUrl(file.download_url)}
                            download
                            className="flex items-center gap-1.5 text-[11px] font-bold text-white bg-emerald-600 hover:bg-emerald-500 px-3 py-2 rounded-lg transition-colors"
                          >
                            <Download size={12} /> Download
                          </a>
                          <button
                            type="button"
                            onClick={() => onDelete(file.document_id)}
                            aria-label={`Delete ${file.file_name}`}
                            className="flex items-center justify-center text-slate-500 hover:text-red-400 hover:bg-red-950/30 p-2 rounded-lg transition-colors"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
