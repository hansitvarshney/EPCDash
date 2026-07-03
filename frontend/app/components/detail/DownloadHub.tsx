'use client';

import { Download, FileSpreadsheet, Clock } from 'lucide-react';
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

export default function DownloadHub({ files }: { files: DownloadFile[] }) {
  return (
    <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800 bg-[#161F30]">
        <h2 className="font-bold text-white text-sm uppercase tracking-wide flex items-center gap-2">
          <FileSpreadsheet size={15} className="text-emerald-400" /> Download Hub
        </h2>
        <p className="text-[11px] text-slate-500 mt-0.5">Generated tracking sheets, with live sync timestamps.</p>
      </div>

      {files.length === 0 ? (
        <div className="p-10 text-center text-xs text-slate-600 font-medium">No tracking sheets generated yet for this site.</div>
      ) : (
        <div className="divide-y divide-slate-800/60">
          {files.map((file) => (
            <div key={file.file_name} className="p-4 flex items-center justify-between gap-4 hover:bg-slate-800/20 transition-colors">
              <div className="min-w-0">
                <p className="text-xs font-bold text-slate-200 truncate">{CATEGORY_LABELS[file.category] || file.category}</p>
                <p className="flex items-center gap-1.5 text-[10px] text-slate-500 mt-1">
                  <Clock size={10} /> Synced {file.last_synced_at} &middot; {formatSize(file.size_bytes)}
                </p>
              </div>
              <a
                href={downloadFileUrl(file.download_url)}
                download
                className="shrink-0 flex items-center gap-1.5 text-[11px] font-bold text-white bg-emerald-600 hover:bg-emerald-500 px-3 py-2 rounded-lg transition-colors"
              >
                <Download size={12} /> Download
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
