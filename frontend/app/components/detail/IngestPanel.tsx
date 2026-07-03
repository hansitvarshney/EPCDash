'use client';

import { useRef, useState } from 'react';
import { UploadCloud, Loader2, X, FileText } from 'lucide-react';
import { ingestDocument } from '../../lib/api';

const CATEGORIES = [
  { value: 'DPR', label: 'Daily Progress Report' },
  { value: 'MATERIAL', label: 'Material Receipt / Consumption' },
  { value: 'BILLING', label: 'Vendor Invoice / Milestone' },
  { value: 'DRAWING', label: 'Drawing Register Entry' },
];

export default function IngestPanel({ siteId, onIngested }: { siteId: number; onIngested: () => void }) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const toggleCategory = (value: string) => {
    setSelectedCategories((prev) => (prev.includes(value) ? prev.filter((c) => c !== value) : [...prev, value]));
  };

  const clearFile = () => {
    setSelectedFile(null);
    setSelectedCategories([]);
    setStatus(null);
  };

  const canUpload = !!selectedFile && selectedCategories.length > 0 && !uploading;

  const handleUpload = async () => {
    if (!selectedFile || selectedCategories.length === 0) return;

    setUploading(true);
    setStatus(`Running the ingestion pipeline for "${selectedFile.name}" across ${selectedCategories.length} sheet type${selectedCategories.length > 1 ? 's' : ''}...`);

    try {
      const result = await ingestDocument(siteId, selectedCategories, selectedFile);
      const summary = result.results
        .map((r) => (r.status === 'success' ? `${r.category}: ${r.exceptions_raised ?? 0} exception(s)` : `${r.category}: failed — ${r.error}`))
        .join('  ·  ');

      const headline =
        result.status === 'success' ? 'Ingested successfully' : result.status === 'partial_success' ? 'Partially ingested' : 'Ingestion failed';
      setStatus(`${headline} — ${summary}`);

      if (result.status !== 'error') {
        onIngested();
      }
      setSelectedFile(null);
      setSelectedCategories([]);
    } catch (err) {
      setStatus(err instanceof Error ? `Ingestion failed: ${err.message}` : 'Ingestion failed.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
      <div>
        <h3 className="text-xs font-bold text-white uppercase tracking-wider">Ingest New Document</h3>
        <p className="text-[11px] text-slate-400 mt-0.5">
          Runs the full Ingestion &rarr; Extraction &rarr; Validation &rarr; Excel Writer pipeline for this site.
        </p>
      </div>

      <input
        type="file"
        ref={inputRef}
        className="hidden"
        accept="image/jpeg,image/png,image/jpg,application/pdf"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            setSelectedFile(file);
            setSelectedCategories([]);
            setStatus(null);
          }
          e.target.value = '';
        }}
      />

      {!selectedFile ? (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="flex items-center gap-2 text-xs font-bold text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700 px-4 py-2.5 rounded-lg transition-colors uppercase tracking-wide"
        >
          <UploadCloud size={13} /> Select Document
        </button>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-3 bg-[#0B0F19] border border-slate-800 rounded-lg px-4 py-2.5">
            <span className="flex items-center gap-2 text-xs font-semibold text-slate-200 truncate">
              <FileText size={13} className="text-blue-400 shrink-0" /> {selectedFile.name}
            </span>
            <button
              type="button"
              onClick={clearFile}
              disabled={uploading}
              className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide text-slate-500 hover:text-red-400 transition-colors shrink-0 disabled:opacity-40"
              aria-label="Remove selected file"
            >
              <X size={13} /> Remove
            </button>
          </div>

          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
              Which sheet(s) are packed inside this document?
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {CATEGORIES.map((c) => {
                const checked = selectedCategories.includes(c.value);
                return (
                  <label
                    key={c.value}
                    className={`flex items-center gap-2 text-xs font-medium px-3 py-2 rounded-lg border cursor-pointer transition-colors ${
                      checked ? 'bg-blue-950/40 border-blue-800/60 text-blue-300' : 'bg-[#0B0F19] border-slate-800 text-slate-400 hover:border-slate-700'
                    } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleCategory(c.value)}
                      disabled={uploading}
                      className="accent-blue-500"
                    />
                    {c.label}
                  </label>
                );
              })}
            </div>
          </div>

          <button
            type="button"
            disabled={!canUpload}
            onClick={handleUpload}
            className="w-full flex items-center justify-center gap-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-xs font-bold px-4 py-2.5 rounded-lg transition-colors uppercase tracking-wide"
          >
            {uploading ? <Loader2 size={13} className="animate-spin" /> : <UploadCloud size={13} />}
            {uploading
              ? 'Processing...'
              : `Upload${selectedCategories.length > 0 ? ` (${selectedCategories.length} sheet${selectedCategories.length > 1 ? 's' : ''})` : ''}`}
          </button>
        </div>
      )}

      {status && <p className="text-xs font-medium text-slate-400">{status}</p>}
    </div>
  );
}
