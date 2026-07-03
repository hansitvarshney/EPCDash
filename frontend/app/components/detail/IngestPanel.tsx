'use client';

import { useRef, useState } from 'react';
import { UploadCloud, Loader2, X, FileText, Images } from 'lucide-react';
import { ingestDocument } from '../../lib/api';

const CATEGORIES = [
  { value: 'DPR', label: 'Daily Progress Report' },
  { value: 'MATERIAL', label: 'Material Receipt / Consumption' },
  { value: 'BILLING', label: 'Vendor Invoice / Milestone' },
  { value: 'DRAWING', label: 'Drawing Register Entry' },
];

function fileKey(file: File): string {
  return `${file.name}_${file.size}_${file.lastModified}`;
}

export default function IngestPanel({ siteId, onIngested }: { siteId: number; onIngested: () => void }) {
  const [files, setFiles] = useState<File[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = (incoming: FileList | File[]) => {
    const accepted = Array.from(incoming).filter((f) =>
      ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'].includes(f.type)
    );
    setFiles((prev) => {
      const existingKeys = new Set(prev.map(fileKey));
      const deduped = accepted.filter((f) => !existingKeys.has(fileKey(f)));
      return [...prev, ...deduped];
    });
    setStatus(null);
  };

  const removeFile = (key: string) => {
    setFiles((prev) => prev.filter((f) => fileKey(f) !== key));
  };

  const clearAll = () => {
    setFiles([]);
    setSelectedCategories([]);
    setStatus(null);
  };

  const toggleCategory = (value: string) => {
    setSelectedCategories((prev) => (prev.includes(value) ? prev.filter((c) => c !== value) : [...prev, value]));
  };

  const canUpload = files.length > 0 && selectedCategories.length > 0 && !uploading;

  const handleUpload = async () => {
    if (files.length === 0 || selectedCategories.length === 0) return;

    setUploading(true);
    setStatus(
      `Running the ingestion pipeline for ${files.length} page${files.length > 1 ? 's' : ''} across ${selectedCategories.length} sheet type${
        selectedCategories.length > 1 ? 's' : ''
      }...`
    );

    try {
      const result = await ingestDocument(siteId, selectedCategories, files);
      const summary = result.results
        .map((r) => (r.status === 'success' ? `${r.category}: ${r.exceptions_raised ?? 0} exception(s)` : `${r.category}: failed — ${r.error}`))
        .join('  ·  ');

      const headline =
        result.status === 'success' ? 'Ingested successfully' : result.status === 'partial_success' ? 'Partially ingested' : 'Ingestion failed';
      setStatus(`${headline} — ${summary}`);

      if (result.status !== 'error') {
        onIngested();
      }
      setFiles([]);
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
          Runs the full Ingestion &rarr; Extraction &rarr; Validation &rarr; Excel Writer pipeline for this site. Stage multiple photos of the
          same report (e.g. sequential WhatsApp images) and they&apos;ll be read together as one cohesive record.
        </p>
      </div>

      <input
        type="file"
        ref={inputRef}
        className="hidden"
        multiple
        accept="image/jpeg,image/png,image/jpg,application/pdf"
        onChange={(e) => {
          if (e.target.files) addFiles(e.target.files);
          e.target.value = '';
        }}
      />

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          if (e.dataTransfer.files) addFiles(e.dataTransfer.files);
        }}
        className={`rounded-lg border-2 border-dashed transition-colors ${
          dragActive ? 'border-blue-500 bg-blue-950/20' : 'border-slate-800'
        } ${files.length === 0 ? 'p-6' : 'p-3'}`}
      >
        {files.length === 0 ? (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="w-full flex flex-col items-center justify-center gap-2 text-xs font-bold text-slate-300 hover:text-white transition-colors"
          >
            <Images size={18} className="text-slate-500" />
            Select or drop image(s) / PDF
            <span className="text-[10px] font-medium normal-case text-slate-500">Add multiple photos of the same report at once</span>
          </button>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                {files.length} page{files.length > 1 ? 's' : ''} staged
              </p>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  disabled={uploading}
                  className="text-[10px] font-bold uppercase tracking-wide text-blue-400 hover:text-blue-300 transition-colors disabled:opacity-40"
                >
                  + Add more
                </button>
                <button
                  type="button"
                  onClick={clearAll}
                  disabled={uploading}
                  className="text-[10px] font-bold uppercase tracking-wide text-slate-500 hover:text-red-400 transition-colors disabled:opacity-40"
                >
                  Clear all
                </button>
              </div>
            </div>

            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
              {files.map((file, idx) => {
                const key = fileKey(file);
                return (
                  <div
                    key={key}
                    className="flex items-center justify-between gap-3 bg-[#0B0F19] border border-slate-800 rounded-lg px-3 py-2"
                  >
                    <span className="flex items-center gap-2 text-xs font-semibold text-slate-200 truncate min-w-0">
                      <span className="text-[10px] font-bold text-slate-600 shrink-0">{String(idx + 1).padStart(2, '0')}</span>
                      <FileText size={13} className="text-blue-400 shrink-0" />
                      <span className="truncate">{file.name}</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => removeFile(key)}
                      disabled={uploading}
                      className="text-slate-500 hover:text-red-400 transition-colors shrink-0 disabled:opacity-40"
                      aria-label={`Remove ${file.name}`}
                    >
                      <X size={14} />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {files.length > 0 && (
        <div className="space-y-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
              Which sheet(s) are packed inside {files.length > 1 ? 'this batch' : 'this document'}?
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
