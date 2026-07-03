'use client';

import { useRef, useState } from 'react';
import { UploadCloud, Loader2 } from 'lucide-react';
import { ingestDocument } from '../../lib/api';

const CATEGORIES = [
  { value: 'DPR', label: 'Daily Progress Report' },
  { value: 'MATERIAL', label: 'Material Receipt / Consumption' },
  { value: 'BILLING', label: 'Vendor Invoice / Milestone' },
  { value: 'DRAWING', label: 'Drawing Register Entry' },
];

export default function IngestPanel({ siteId, onIngested }: { siteId: number; onIngested: () => void }) {
  const [category, setCategory] = useState('DPR');
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setUploading(true);
    setStatus(`Running the ingestion pipeline for "${file.name}"...`);
    try {
      const result = await ingestDocument(siteId, category, file);
      setStatus(
        result.exceptions_raised > 0
          ? `Ingested successfully — ${result.exceptions_raised} exception(s) flagged for review.`
          : 'Ingested successfully — no exceptions raised.'
      );
      onIngested();
    } catch (err) {
      setStatus(err instanceof Error ? `Ingestion failed: ${err.message}` : 'Ingestion failed.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">Ingest New Document</h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Runs the full Ingestion &rarr; Extraction &rarr; Validation &rarr; Excel Writer pipeline for this site.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            disabled={uploading}
            className="bg-[#1F2937] border border-slate-700 text-white rounded-lg px-3 py-2 text-xs font-semibold focus:outline-hidden focus:border-blue-500"
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
          <input
            type="file"
            ref={inputRef}
            className="hidden"
            accept="image/jpeg,image/png,image/jpg,application/pdf"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
              e.target.value = '';
            }}
          />
          <button
            type="button"
            disabled={uploading}
            onClick={() => inputRef.current?.click()}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white text-xs font-bold px-4 py-2 rounded-lg transition-colors uppercase tracking-wide"
          >
            {uploading ? <Loader2 size={13} className="animate-spin" /> : <UploadCloud size={13} />}
            {uploading ? 'Processing...' : 'Upload'}
          </button>
        </div>
      </div>
      {status && <p className="text-xs font-medium text-slate-400">{status}</p>}
    </div>
  );
}
