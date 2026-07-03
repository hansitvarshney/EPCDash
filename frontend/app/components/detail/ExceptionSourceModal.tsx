'use client';

import { X, FileText, Hash, Quote } from 'lucide-react';
import { ExceptionAlert } from '../../lib/api';

export default function ExceptionSourceModal({ alert, onClose }: { alert: ExceptionAlert; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-[#111827] border border-slate-800 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-slate-800 bg-[#161F30] flex items-center justify-between">
          <h3 className="text-sm font-bold text-white uppercase tracking-wide">Source Citation</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">Exception</p>
            <p className="text-sm text-slate-200 leading-relaxed">{alert.message}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#0B0F19] border border-slate-800/80 rounded-lg p-4">
              <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                <FileText size={11} /> Document
              </p>
              <p className="text-xs font-bold text-slate-200 break-words">{alert.source_citation.document_name || 'Not attached'}</p>
            </div>
            <div className="bg-[#0B0F19] border border-slate-800/80 rounded-lg p-4">
              <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                <Hash size={11} /> Page
              </p>
              <p className="text-xs font-bold text-slate-200">{alert.source_citation.page_number ?? '—'}</p>
            </div>
          </div>

          <div className="bg-[#0B0F19] border border-slate-800/80 rounded-lg p-4">
            <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
              <Quote size={11} /> Source Text Snippet
            </p>
            <p className="text-xs text-slate-300 leading-relaxed italic">
              &ldquo;{alert.source_citation.text_snippet || 'No snippet captured.'}&rdquo;
            </p>
          </div>

          <div className="flex items-center justify-between text-[10px] text-slate-600 font-mono pt-2 border-t border-slate-800/60">
            <span>Exception #{alert.id}</span>
            <span>{alert.related_table ? `${alert.related_table}#${alert.related_record_id}` : ''}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
